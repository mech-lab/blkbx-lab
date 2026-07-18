require "rails_helper"

RSpec.describe "MAND8 dashboard", type: :request do
  it "renders underwriter-facing case summaries for the current workspace" do
    SchemaCatalog.seed_defaults!

    user = create(:user)
    organization = create(:organization)
    create(:membership, user: user, organization: organization, role: "owner")
    workspace = create(:workspace, organization: organization, product_type: "mand8")

    Mand8::SeedDemoWorkspace.call(workspace: workspace, scenario: "lloyds_incident_to_renewal", actor: user)

    sign_in user
    get "/api/v1/mand8/dashboard",
        params: { workspace_id: workspace.id },
        headers: { "HOST" => "app.mand8.ai" }

    expect(response).to have_http_status(:ok)
    parsed = JSON.parse(response.body)
    expect(parsed.dig("summary", "case_count")).to eq(1)
    expect(parsed.dig("cases", 0, "case_id")).to eq("case_mand8_lloyds_incident_003")
    expect(parsed.dig("cases", 0, "authority_status")).to eq("within_authority")
    expect(parsed.dig("cases", 0, "incident_count")).to eq(1)
    expect(parsed.dig("cases", 0, "latest_verification_status")).to eq("warning")
    expect(parsed.dig("verifier_handoff", "product")).to eq("mand8")
    expect(parsed.dig("verifier_handoff", "available")).to eq(false)
    expect(parsed.dig("verifier_handoff", "reason_code")).to eq("PORTABLE_RECEIPT_MISSING")
    expect(parsed.dig("verifier_handoff", "artifact_url")).to be_nil
    expect(parsed.dig("cases", 0, "verifier_handoff", "available")).to eq(false)
    expect(parsed.dig("cases", 0, "verifier_handoff", "reason_code")).to eq("PORTABLE_RECEIPT_MISSING")
    expect(parsed.dig("cases", 0, "verifier_handoff", "verify_path")).to be_nil
  end
end
