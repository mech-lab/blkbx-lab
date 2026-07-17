module Due
  class CreateDisclosureReceipt
    def self.call(organization:, workspace:, actor: nil, body: {}, domain_metadata: {})
      Ink::IssueReceipt.call(
        organization: organization,
        workspace: workspace,
        actor: actor,
        workflow_kind: "disclosure",
        schema_key: "due.disclosure_receipt.v1",
        schema_version: "1.0.0",
        body: body,
        domain_metadata: domain_metadata
      )
    end
  end
end
