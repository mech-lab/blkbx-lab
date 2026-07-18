require "open3"
require "shellwords"
require "tempfile"

module Ink
  class VerifyReceipt
    def self.call(options = {})
      new(options).call
    end

    def initialize(options = {})
      @receipt = options.fetch(:receipt)
      @verification_policy = options.fetch(:verification_policy)
      @evidence_bundle = options[:evidence_bundle]
    end

    def call
      command = ENV.fetch("INK_VERIFY_COMMAND", "cargo run --quiet -p ink-cli -- receipt")
      report_json, status, error_message = run_command(command)

      VerificationRun.create!(
        organization: @receipt.organization,
        workspace: @receipt.workspace,
        receipt: @receipt,
        evidence_bundle: @evidence_bundle,
        verification_policy: @verification_policy,
        status: status,
        report_json: report_json,
        error_message: error_message,
        verified_at: Time.current
      ).tap do |run|
        AuditEvent.record!("receipt.verified", auditable: run, organization: @receipt.organization, workspace: @receipt.workspace, user: Current.user, api_credential: Current.api_credential, request_id: Current.request_id, resulting_state: run.attributes)
      end
    end

    private

    def run_command(base_command)
      receipt_file = Tempfile.new(["receipt", ".json"])
      policy_file = Tempfile.new(["policy", ".json"])
      receipt_file.write(JSON.pretty_generate(@receipt.portable_receipt || @receipt.body_json))
      policy_file.write(JSON.pretty_generate(@verification_policy.policy_json))
      receipt_file.flush
      policy_file.flush

      stdout, stderr, process = Open3.capture3("#{base_command} --receipt #{Shellwords.escape(receipt_file.path)} --policy #{Shellwords.escape(policy_file.path)}")
      status = process.success? ? "passed" : "failed"
      parsed = stdout.present? ? JSON.parse(stdout) : { "status" => status, "stderr" => stderr }
      [parsed, status, stderr.presence]
    rescue StandardError => error
      [{ "status" => "error", "message" => error.message }, "error", error.message]
    ensure
      receipt_file&.close!
      policy_file&.close!
    end
  end
end
