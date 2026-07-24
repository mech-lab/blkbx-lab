module Blkbxs
  class VerifierArtifacts
    def self.call(workspace:, business_process_id: nil, bundle_id: nil, receipt_id: nil)
      new(workspace: workspace, business_process_id: business_process_id, bundle_id: bundle_id, receipt_id: receipt_id).call
    end

    def initialize(workspace:, business_process_id:, bundle_id:, receipt_id:)
      @workspace = workspace
      @business_process_id = business_process_id.presence
      @bundle_id = bundle_id.presence
      @receipt_id = receipt_id.presence
    end

    def call
      bundle = selected_bundle
      records = selected_receipts(bundle)
      raise ActiveRecord::RecordNotFound, "No BLKBXS UBR receipts found for verifier handoff" if records.empty?
      raise ActiveRecord::RecordNotFound, "No linked portable ink.receipt.v2 found for verifier handoff" if records.any? { |record| record.portable_receipt.blank? }

      terminal = terminal_receipt(records)
      {
        "receipt" => terminal.portable_receipt,
        "receipt_graph" => records.map do |record|
          {
            "receipt_id" => record.id,
            "ubr_receipt_id" => UbrGraph.receipt_id(record),
            "operation_name" => record.body_json.dig("operation", "name"),
            "portable_receipt" => record.portable_receipt,
            "portable_manifest" => portable_manifest(record)
          }
        end,
        "reviewer_packet" => reviewer_packet_manifest(records: records, bundle: bundle),
        "context" => {
          "product" => "blkbxs",
          "workspace_id" => @workspace.id,
          "business_process_id" => resolved_business_process_id(records, bundle),
          "bundle_id" => bundle&.id,
          "receipt_id" => terminal.id,
          "title" => bundle&.title || "BLKBXS UBR verifier handoff",
          "terminal_ubr_receipt_id" => UbrGraph.receipt_id(terminal)
        }.compact
      }
    end

    private

    def selected_bundle
      return @workspace.evidence_bundles.find(@bundle_id) if @bundle_id
      return @workspace.evidence_bundles.detect { |record| record.manifest["business_process_id"] == @business_process_id } if @business_process_id
      return @workspace.evidence_bundles.joins(:receipts).where(receipts: { id: @receipt_id }).order(created_at: :desc).first if @receipt_id

      @workspace.evidence_bundles.where(bundle_type: "blkbxs_ubr_graph").order(created_at: :desc).first
    end

    def selected_receipts(bundle)
      scope = @workspace.receipts.where(schema_key: WorkspaceSnapshot::UBR_SCHEMA)
      if @receipt_id
        return [scope.find(@receipt_id)]
      end
      if @business_process_id
        return scope.select { |record| WorkspaceSnapshot.business_process_id_for_receipt(record) == @business_process_id }
      end
      if bundle
        return bundle.receipts.where(schema_key: WorkspaceSnapshot::UBR_SCHEMA).to_a
      end

      process_id = scope.map { |record| WorkspaceSnapshot.business_process_id_for_receipt(record) }.compact.uniq.sort.first
      return [] unless process_id

      scope.select { |record| WorkspaceSnapshot.business_process_id_for_receipt(record) == process_id }
    end

    def terminal_receipt(records)
      validation = UbrGraph.validate(records)
      terminal_id = validation["terminal_receipts"].last
      records.find { |record| UbrGraph.receipt_id(record) == terminal_id } || records.max_by { |record| record.created_at || Time.at(0) }
    end

    def resolved_business_process_id(records, bundle)
      @business_process_id ||
        bundle&.manifest&.[]("business_process_id") ||
        records.map { |record| WorkspaceSnapshot.business_process_id_for_receipt(record) }.compact.first
    end

    def portable_manifest(receipt)
      receipt.evidence_bundles.order(created_at: :desc).map(&:manifest).find { |manifest| manifest.is_a?(Hash) && manifest["schema"] == "ink.manifest.v2" }
    end

    def reviewer_packet_manifest(records:, bundle:)
      {
        "schema" => "blkbxs.ubr.reviewer_packet.v1",
        "profile" => "blkbxs.bank_credit_reviewer_packet",
        "business_process_id" => resolved_business_process_id(records, bundle),
        "bundle_id" => bundle&.id,
        "receipt_count" => records.length,
        "portable_receipt_required" => true,
        "instructions" => [
          "Verify each linked ink.receipt.v2 portable receipt with the native INK verifier.",
          "Treat UBR-native demo verification fields as domain evidence only, not as the trust root.",
          "Review graph validation, evidence disclosure, and AI/human boundary summaries before accepting the banking event chain."
        ]
      }
    end
  end
end
