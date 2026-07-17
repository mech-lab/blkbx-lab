module Due
  class CreatePrivilegeReceipt
    def self.call(organization:, workspace:, actor: nil, body: {}, domain_metadata: {})
      Ink::IssueReceipt.call(
        organization: organization,
        workspace: workspace,
        actor: actor,
        workflow_kind: "privilege",
        schema_key: "due.privilege_receipt.v1",
        schema_version: "1.0.0",
        body: body,
        domain_metadata: domain_metadata
      )
    end
  end
end
