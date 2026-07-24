module Blkbxs
  class WorkspaceSnapshot
    UBR_SCHEMA = "blkbxs.ubr.receipt.v1".freeze

    def self.call(workspace)
      new(workspace).call
    end

    def self.business_process_id_for_receipt(receipt)
      receipt.domain_metadata["business_process_id"] || UbrGraph.business_process_id(receipt)
    end

    def self.application_id_for_receipt(receipt)
      receipt.domain_metadata["application_id"] || UbrGraph.application_id(receipt)
    end

    def self.graph_summary_for_bundle(bundle, business_process_id: nil)
      new(bundle.workspace).graph_summary(business_process_id || bundle.manifest["business_process_id"])
    end

    def initialize(workspace)
      @workspace = workspace
    end

    def call
      graphs = business_process_ids.map { |business_process_id| graph_summary(business_process_id) }
      {
        workspace: @workspace.as_json(only: %i[id name slug product_type active metadata]),
        summary: {
          graph_count: graphs.length,
          receipt_count: graphs.sum { |item| item["receipt_count"] },
          review_request_count: @workspace.review_requests.count,
          latest_verification_status: @workspace.verification_runs.recent.first&.status
        },
        graphs: graphs,
        demo_scenarios: DemoCatalog.available_scenarios,
        verifier_handoff: VerifierHandoff.payload(workspace: @workspace)
      }
    end

    def graph_summary(business_process_id)
      receipts = receipts_for_process(business_process_id)
      bundles = @workspace.evidence_bundles.select { |bundle| bundle.manifest["business_process_id"] == business_process_id }
      review_requests = @workspace.review_requests.select { |request| request.evidence_bundle&.manifest&.[]("business_process_id") == business_process_id }
      validation = UbrGraph.validate(receipts)
      {
        "business_process_id" => business_process_id,
        "application_id" => receipts.map { |receipt| self.class.application_id_for_receipt(receipt) }.compact.first,
        "receipt_count" => receipts.length,
        "graph_valid" => validation["valid"],
        "graph_order" => validation["topological_order"],
        "decision_summary" => UbrGraph.decision_summary(receipts),
        "ai_boundary_summary" => validation["ai_boundary_summary"],
        "latest_verification_status" => receipts.flat_map(&:verification_runs).max_by { |run| run.verified_at || Time.at(0) }&.status,
        "review_request_statuses" => review_requests.map(&:status).uniq,
        "receipts" => receipts.map do |receipt|
          {
            "id" => receipt.id,
            "schema_key" => receipt.schema_key,
            "workflow_kind" => receipt.workflow_kind,
            "external_id" => receipt.external_id,
            "ubr_receipt_id" => UbrGraph.receipt_id(receipt),
            "business_process_id" => self.class.business_process_id_for_receipt(receipt),
            "portable_receipt_available" => receipt.portable_receipt.present?
          }
        end,
        "bundle_ids" => bundles.map(&:id),
        "verifier_handoff" => VerifierHandoff.payload(workspace: @workspace, business_process_id: business_process_id)
      }
    end

    private

    def business_process_ids
      @workspace.receipts.where(schema_key: UBR_SCHEMA).map { |receipt| self.class.business_process_id_for_receipt(receipt) }.compact.uniq.sort
    end

    def receipts_for_process(business_process_id)
      @workspace.receipts.where(schema_key: UBR_SCHEMA).select { |receipt| self.class.business_process_id_for_receipt(receipt) == business_process_id }
    end
  end
end
