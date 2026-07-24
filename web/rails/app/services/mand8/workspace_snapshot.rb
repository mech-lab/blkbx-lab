module Mand8
  class WorkspaceSnapshot
    RISK_SCHEMA = "mand8.risk_receipt.v1".freeze
    AUTHORITY_SCHEMA = "mand8.authority_receipt.v1".freeze
    INCIDENT_SCHEMA = "mand8.incident_receipt.v1".freeze

    def self.call(workspace)
      new(workspace).call
    end

    def self.case_id_for_receipt(receipt)
      receipt.body_json["case_id"] ||
        receipt.body_json.dig("domain_context", "case_id") ||
        receipt.domain_metadata["case_id"]
    end

    def self.case_summary_for_bundle(bundle, case_id: nil)
      workspace = bundle.workspace
      summary = new(workspace).case_summary(case_id || bundle.manifest["case_id"])
      summary.merge(
        "bundle" => bundle.as_json,
        "bundle_manifest" => bundle.manifest
      )
    end

    def initialize(workspace)
      @workspace = workspace
    end

    def call
      cases = case_ids.map { |case_id| case_summary(case_id) }
      {
        workspace: @workspace.as_json(only: %i[id name slug product_type active metadata]),
        summary: {
          case_count: cases.length,
          review_request_count: @workspace.review_requests.count,
          ready_for_renewal_count: cases.count { |item| item["renewal_ready"] },
          open_incident_count: cases.sum { |item| item["incident_count"] },
          latest_verification_status: @workspace.verification_runs.recent.first&.status
        },
        cases: cases,
        demo_scenarios: DemoCatalog.available_scenarios.map do |scenario|
          definition = DemoCatalog.fetch(scenario)
          {
            key: scenario,
            name: definition.dig("workspace", "name"),
            slug: definition.dig("workspace", "slug")
          }
        end,
        verifier_handoff: VerifierHandoff.payload(workspace: @workspace)
      }
    end

    def case_summary(case_id)
      receipts = receipts_for_case(case_id)
      risk_receipt = receipts.find { |receipt| receipt.schema_key == RISK_SCHEMA }
      authority_receipts = receipts.select { |receipt| receipt.schema_key == AUTHORITY_SCHEMA }
      incident_receipts = receipts.select { |receipt| receipt.schema_key == INCIDENT_SCHEMA }
      bundles = @workspace.evidence_bundles.select { |bundle| bundle.manifest["case_id"] == case_id }
      review_requests = @workspace.review_requests.select { |request| request.evidence_bundle&.manifest&.[]("case_id") == case_id }
      verification_runs = receipts.flat_map(&:verification_runs).sort_by { |run| run.verified_at || Time.at(0) }
      defensibility_annotation = ActuarialAnnotation.call(receipts: receipts, verification_reports: verification_runs)

      event_trail = Array(risk_receipt&.body_json&.[]("event_trail"))
      latest_incident_payload = incident_receipts.last&.body_json || event_payloads(event_trail, "incident_recorded").last || {}

      {
        "case_id" => case_id,
        "policy_ref" => risk_receipt&.body_json&.dig("domain_context", "policy_ref") || authority_receipts.last&.body_json&.dig("domain_context", "policy_ref"),
        "binder_ref" => risk_receipt&.body_json&.dig("domain_context", "binder_ref") || authority_receipts.last&.body_json&.dig("domain_context", "binder_ref"),
        "managing_agent" => risk_receipt&.body_json&.dig("domain_context", "managing_agent") || authority_receipts.last&.body_json&.dig("domain_context", "managing_agent"),
        "coverholder" => risk_receipt&.body_json&.dig("domain_context", "coverholder") || authority_receipts.last&.body_json&.dig("domain_context", "coverholder"),
        "authority_status" => authority_receipts.last&.body_json&.dig("authority_scope", "status") || risk_receipt&.body_json&.dig("domain_context", "authority_status"),
        "human_review_status" => risk_receipt&.body_json&.dig("human_review", "status") || authority_receipts.last&.body_json&.dig("human_review", "status"),
        "control_check_count" => event_payloads(event_trail, "control_check_recorded").count,
        "override_count" => event_payloads(event_trail, "override_recorded").count,
        "incident_count" => incident_receipts.count + event_payloads(event_trail, "incident_recorded").count,
        "latest_incident_severity" => latest_incident_payload["severity"],
        "latest_verification_status" => verification_runs.last&.status,
        "renewal_ready" => bundles.any? { |bundle| bundle.manifest.dig("underwriter_summary", "renewal_ready") } || (
          (authority_receipts.last&.body_json&.dig("authority_scope", "status") || risk_receipt&.body_json&.dig("domain_context", "authority_status")) == "within_authority" &&
          (risk_receipt&.body_json&.dig("human_review", "status") || "not_reviewed") == "reviewed" &&
          incident_receipts.empty? &&
          event_payloads(event_trail, "incident_recorded").empty? &&
          event_payloads(event_trail, "control_check_recorded").any?
        ),
        "review_request_statuses" => review_requests.map(&:status).uniq,
        "receipts" => receipts.map do |receipt|
          {
            "id" => receipt.id,
            "schema_key" => receipt.schema_key,
            "workflow_kind" => receipt.workflow_kind,
            "external_id" => receipt.external_id,
            "case_id" => self.class.case_id_for_receipt(receipt)
          }
        end,
        "bundle_ids" => bundles.map(&:id),
        "defensibility_annotation" => defensibility_annotation,
        "verifier_handoff" => VerifierHandoff.payload(workspace: @workspace, case_id: case_id)
      }
    end

    private

    def case_ids
      @workspace.receipts.filter_map { |receipt| self.class.case_id_for_receipt(receipt) }.uniq.sort
    end

    def receipts_for_case(case_id)
      @workspace.receipts.select { |receipt| self.class.case_id_for_receipt(receipt) == case_id }
    end

    def event_payloads(event_trail, event_type)
      event_trail.filter_map do |entry|
        payload = entry["payload"] || {}
        payload if entry["event_type"] == event_type
      end
    end
  end
end
