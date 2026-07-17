module Mand8
  class CreateInsurabilityReceipt
    def self.call(organization:, workspace:, actor: nil, body: {}, domain_metadata: {})
      normalized_body = ReceiptContract.insurability(body: body, domain_metadata: domain_metadata)
      Ink::IssueReceipt.call(
        organization: organization,
        workspace: workspace,
        actor: actor,
        workflow_kind: "insurability",
        schema_key: "mand8.risk_receipt.v1",
        schema_version: "1.0.0",
        body: normalized_body,
        domain_metadata: domain_metadata.merge(
          case_id: normalized_body["case_id"],
          policy_ref: normalized_body.dig("domain_context", "policy_ref"),
          binder_ref: normalized_body.dig("domain_context", "binder_ref")
        )
      )
    end
  end
end
