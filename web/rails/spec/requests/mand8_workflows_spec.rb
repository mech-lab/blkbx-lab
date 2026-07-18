require "rails_helper"

RSpec.describe "MAND8 workflows", type: :request do
  it "creates case-linked receipts, bundles them, and opens a carrier review request" do
    SchemaCatalog.seed_defaults!
    WorkflowCatalog.seed_defaults!

    user = create(:user)
    organization = create(:organization)
    create(:membership, user: user, organization: organization, role: "owner")
    workspace = create(:workspace, organization: organization, product_type: "mand8")

    sign_in user

    post "/api/v1/mand8/insurability_receipts",
         params: {
           workspace_id: workspace.id,
           body_json: {
             domain_context: {
               exposure_unit_id: "uk-cyber-eu-900",
               policy_ref: "B900UK2026",
               risk_class: "cyber",
               insured_value: 900000.0,
               binder_ref: "B900UK2026",
               managing_agent: "Lime Street Managing Agency Ltd"
             },
             decision: "bind_with_controls"
           }
         },
         headers: { "HOST" => "app.mand8.ai" }
    expect(response).to have_http_status(:created)
    risk_receipt = JSON.parse(response.body)
    case_id = risk_receipt.dig("body_json", "case_id")
    expect(case_id).to be_present
    expect(risk_receipt.fetch("schema_key")).to eq("mand8.risk_receipt.v1")

    post "/api/v1/mand8/authority_receipts",
         params: {
           workspace_id: workspace.id,
           body_json: {
             case_id: case_id,
             policy_ref: "B900UK2026",
             binder_ref: "B900UK2026",
             authority_id: "auth-900",
             managing_agent: "Lime Street Managing Agency Ltd"
           }
         },
         headers: { "HOST" => "app.mand8.ai" }
    expect(response).to have_http_status(:created)
    authority_receipt = JSON.parse(response.body)
    expect(authority_receipt.fetch("schema_key")).to eq("mand8.authority_receipt.v1")
    expect(authority_receipt.dig("body_json", "case_id")).to eq(case_id)

    post "/api/v1/mand8/incident_receipts",
         params: {
           workspace_id: workspace.id,
           body_json: {
             case_id: case_id,
             incident_id: "inc-900-01",
             incident_type: "drift_alert",
             severity: "medium",
             description: "Monitoring drift event",
             claims_impact: "monitor_for_renewal"
           }
         },
         headers: { "HOST" => "app.mand8.ai" }
    expect(response).to have_http_status(:created)
    incident_receipt = JSON.parse(response.body)
    expect(incident_receipt.dig("body_json", "case_id")).to eq(case_id)

    post "/api/v1/mand8/renewal_bundles",
         params: {
           workspace_id: workspace.id,
           title: "Renewal evidence bundle",
           receipt_ids: [
             risk_receipt.fetch("id"),
             authority_receipt.fetch("id"),
             incident_receipt.fetch("id")
           ]
         },
         headers: { "HOST" => "app.mand8.ai" }
    expect(response).to have_http_status(:created)
    bundle = JSON.parse(response.body)
    expect(bundle.dig("manifest", "case_id")).to eq(case_id)
    expect(bundle.dig("manifest", "underwriter_summary", "incident_count")).to eq(1)
    expect(bundle.dig("manifest", "verifier_handoff", "available")).to eq(false)
    expect(bundle.dig("manifest", "verifier_handoff", "reason_code")).to eq("PORTABLE_RECEIPT_MISSING")
    expect(bundle.dig("manifest", "verifier_handoff", "artifact_url")).to be_nil

    post "/api/v1/mand8/carrier_review_requests",
         params: {
           workspace_id: workspace.id,
           evidence_bundle_id: bundle.fetch("id"),
           title: "Carrier review",
           reviewer: {
             email: "carrier@mand8.example",
             name: "Carrier Reviewer",
             role: "lloyds_underwriter"
           }
         },
         headers: { "HOST" => "app.mand8.ai" }
    expect(response).to have_http_status(:created)
    review_request = JSON.parse(response.body)
    expect(review_request.dig("shared_bundle", "status")).to eq("active")

    post "/api/v1/mand8/incident_receipts",
         params: {
           workspace_id: workspace.id,
           body_json: {
             case_id: "case_other_001",
             incident_id: "inc-other-01",
             incident_type: "drift_alert",
             severity: "high",
             description: "Other case incident"
           }
         },
         headers: { "HOST" => "app.mand8.ai" }
    mismatched = JSON.parse(response.body)

    post "/api/v1/mand8/renewal_bundles",
         params: {
           workspace_id: workspace.id,
           title: "Invalid bundle",
           receipt_ids: [
             risk_receipt.fetch("id"),
             mismatched.fetch("id")
           ]
         },
         headers: { "HOST" => "app.mand8.ai" }
    expect(response).to have_http_status(:unprocessable_entity)
    expect(JSON.parse(response.body).fetch("error")).to include("single case")
  end
end
