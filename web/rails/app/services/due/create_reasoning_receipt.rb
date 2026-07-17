module Due
  class CreateReasoningReceipt
    def self.call(organization:, workspace:, actor: nil, body: {}, domain_metadata: {})
      Ink::IssueReceipt.call(
        organization: organization,
        workspace: workspace,
        actor: actor,
        workflow_kind: "reasoning",
        schema_key: "due.legal_action_receipt.v1",
        schema_version: "1.0.0",
        body: body,
        domain_metadata: domain_metadata
      )
    end
  end
end
