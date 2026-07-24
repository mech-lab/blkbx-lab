module Blkbxs
  class CreateUbrReceipt
    def self.call(organization:, workspace:, actor: nil, body: {}, domain_metadata: {})
      normalized_body = ReceiptContract.ubr_event(body: body, domain_metadata: domain_metadata)
      metadata = ReceiptContract.domain_metadata_for(body: normalized_body, domain_metadata: domain_metadata)

      Ink::IssueReceipt.call(
        organization: organization,
        workspace: workspace,
        actor: actor,
        workflow_kind: "ubr_event",
        schema_key: "blkbxs.ubr.receipt.v1",
        schema_version: "1.0.0",
        body: normalized_body,
        domain_metadata: metadata,
        external_id: normalized_body.fetch("id"),
        title: "BLKBXS UBR #{normalized_body.dig('operation', 'name')}",
        require_portable_receipt: true
      )
    end
  end
end
