require "rails_helper"

RSpec.describe "Workspace selection and seeding", type: :request do
  it "selects a workspace and seeds a MAND8 demo scenario" do
    user = create(:user)
    organization = create(:organization)
    create(:membership, user: user, organization: organization, role: "owner")
    workspace = create(
      :workspace,
      organization: organization,
      product_type: "mand8",
      metadata: { "demo_scenario" => "lloyds_cyber_happy_path" }
    )

    sign_in user
    post "/api/v1/organizations/#{organization.id}/workspaces/#{workspace.id}/seed_demo",
         params: { scenario: "lloyds_cyber_happy_path" },
         headers: { "HOST" => "app.mand8.ai" }

    expect(response).to have_http_status(:ok)
    seeded = JSON.parse(response.body)
    expect(seeded.dig("seed_result", "case_id")).to eq("case_mand8_lloyds_happy_001")
    expect(workspace.reload.receipts.count).to be >= 2

    post "/api/v1/organizations/#{organization.id}/workspaces/#{workspace.id}/select",
         headers: { "HOST" => "app.mand8.ai" }

    expect(response).to have_http_status(:ok)
    selected = JSON.parse(response.body)
    expect(selected.fetch("selected")).to eq(true)
    expect(selected.dig("selection", "workspace_id")).to eq(workspace.id)
    expect(selected.dig("mand8", "summary", "case_count")).to eq(1)
  end
end
