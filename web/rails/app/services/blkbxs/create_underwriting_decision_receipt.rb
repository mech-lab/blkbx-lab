module Blkbxs
  class CreateUnderwritingDecisionReceipt
    def self.call(organization:, workspace:, actor: nil, body: {}, domain_metadata: {})
      Ink::IssueReceipt.call(
        organization: organization,
        workspace: workspace,
        actor: actor,
        workflow_kind: "underwriting_decision",
        schema_key: "blkbxs.underwriting_decision_receipt.v1",
        schema_version: "1.0.0",
        body: body,
        domain_metadata: domain_metadata
      )
    end
  end
end
