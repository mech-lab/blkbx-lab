module Blkbxs
  class BuildUbrBundle
    def self.call(organization:, workspace:, actor: nil, receipts:, title: "UBR loan evidence graph", workflow_run: nil, evidence_manifest: nil, verifier_report: nil)
      ApplicationRecord.transaction do
        bundle = Ink::BuildBundle.call(
          organization: organization,
          workspace: workspace,
          actor: actor,
          receipts: receipts,
          title: title.presence || "UBR loan evidence graph",
          workflow_run: workflow_run,
          bundle_type: "blkbxs_ubr_graph"
        )
        update_manifest!(
          bundle: bundle,
          workspace: workspace,
          receipts: receipts,
          evidence_manifest: evidence_manifest,
          verifier_report: verifier_report
        )
      end
    end

    def self.update_manifest!(bundle:, workspace:, receipts:, evidence_manifest: nil, verifier_report: nil)
      records = Array(receipts)
      raise ArgumentError, "BLKBXS UBR bundles require at least one UBR receipt" if records.empty?
      raise ArgumentError, "BLKBXS UBR bundles require every receipt to use blkbxs.ubr.receipt.v1" if records.any? { |receipt| receipt.schema_key != WorkspaceSnapshot::UBR_SCHEMA }

      unsigned = records.reject { |receipt| receipt.portable_receipt.present? }
      if unsigned.any?
        raise ArgumentError, "BLKBXS UBR bundles require every receipt to have a linked ink.receipt.v2 portable receipt"
      end

      validation = UbrGraph.validate(records, evidence_manifest: evidence_manifest, verifier_report: verifier_report)
      raise ArgumentError, "BLKBXS UBR graph is invalid: #{validation['failures'].map { |failure| failure['code'] }.join(', ')}" unless validation["valid"]

      business_process_id = validation.fetch("business_process_id")
      decision = UbrGraph.decision_summary(records, verifier_report)
      updated_manifest = bundle.manifest.merge(
        "product_type" => "blkbxs",
        "schema" => "blkbxs.ubr.bundle.v1",
        "business_process_id" => business_process_id,
        "application_id" => decision["application_id"],
        "graph_validation" => validation,
        "graph_order" => validation["topological_order"],
        "decision_summary" => decision,
        "evidence_summary" => validation["evidence_summary"],
        "ai_boundary_summary" => validation["ai_boundary_summary"],
        "verifier_report_summary" => UbrGraph.verifier_report_summary(verifier_report),
        "receipt_summaries" => records.map do |receipt|
          {
            "id" => receipt.id,
            "schema_key" => receipt.schema_key,
            "workflow_kind" => receipt.workflow_kind,
            "external_id" => receipt.external_id,
            "ubr_receipt_id" => UbrGraph.receipt_id(receipt),
            "operation_name" => receipt.body_json.dig("operation", "name"),
            "business_process_id" => WorkspaceSnapshot.business_process_id_for_receipt(receipt),
            "portable_receipt_available" => receipt.portable_receipt.present?
          }
        end,
        "demo_verifier_report" => verifier_report.present?,
        "verifier_handoff" => VerifierHandoff.payload(
          workspace: workspace,
          business_process_id: business_process_id,
          bundle_id: bundle.id
        )
      )
      updated_manifest["evidence_manifest"] = evidence_manifest if evidence_manifest.present?
      bundle.update!(
        manifest: updated_manifest,
        sha256: Digest::SHA256.hexdigest(JSON.generate(updated_manifest))
      )
      bundle
    end
  end
end
