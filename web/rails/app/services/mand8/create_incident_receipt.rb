module Mand8
  class CreateIncidentReceipt
    def self.call(organization:, workspace:, actor: nil, body: {}, domain_metadata: {})
      normalized_body = ReceiptContract.incident(body: body, domain_metadata: domain_metadata)
      Ink::IssueReceipt.call(
        organization: organization,
        workspace: workspace,
        actor: actor,
        workflow_kind: "incident",
        schema_key: "mand8.incident_receipt.v1",
        schema_version: "1.0.0",
        body: normalized_body,
        domain_metadata: domain_metadata.merge(
          case_id: normalized_body["case_id"],
          incident_id: normalized_body["incident_id"]
        )
      )
    end
  end
end
