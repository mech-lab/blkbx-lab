module Blkbxs
  module Sprint
    class RunVerification
      def self.call(options = {})
        new(options).call
      end

      def initialize(options = {})
        @loan_case = options.fetch(:loan_case)
        @evidence_bundle = options[:evidence_bundle]
      end

      def call
        receipt = terminal_receipt
        raise ArgumentError, "BLKBXS sprint verification requires a signed terminal receipt" unless receipt&.portable_receipt.present?

        run = Ink::VerifyReceipt.call(
          receipt: receipt,
          verification_policy: verification_policy,
          evidence_bundle: @evidence_bundle || @loan_case.latest_evidence_bundle
        )
        @loan_case.update!(status: status_for(run.status))
        run
      end

      private

      def terminal_receipt
        receipts = @loan_case.receipts.to_a
        validation = UbrGraph.validate(receipts)
        terminal_id = validation["terminal_receipts"].last
        receipts.find { |receipt| UbrGraph.receipt_id(receipt) == terminal_id } || receipts.max_by(&:created_at)
      end

      def verification_policy
        @loan_case.workspace.verification_policies.active.first || @loan_case.workspace.verification_policies.create!(
          organization: @loan_case.organization,
          name: "BLKBXS sprint local verifier policy",
          active: true,
          policy_json: {
            "schema" => "ink.verify-policy.v1",
            "policy_id" => "BLKBXS_SPRINT_LOCAL",
            "require_canonical_tlv_v2" => true,
            "allow_verify_only_formats" => false,
            "require_trusted_issuer" => false,
            "require_revocation_check" => false,
            "require_manifest_hash_match_when_manifest_present" => true,
            "require_evidence_summary_match_when_manifest_present" => true,
            "require_controls_summary_match_when_controls_present" => true,
            "allow_network" => false
          },
          trust_anchors: [],
          allowed_issuers: [],
          required_claims: []
        )
      end

      def status_for(run_status)
        case run_status
        when "passed" then "verification_passed"
        when "failed" then "verification_failed"
        else "verification_failed"
        end
      end
    end
  end
end
