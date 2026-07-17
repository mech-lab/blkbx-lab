require "rails_helper"

RSpec.describe "Session handoffs", type: :request do
  it "issues a one-time handoff for a target branded host" do
    user = create(:user)
    organization = create(:organization)
    workspace = create(:workspace, organization: organization, product_type: "ink")
    create(:membership, user: user, organization: organization, role: "owner")

    sign_in user
    post "/accounts/session_handoffs",
         params: { target_host: "app.blkbxs.xyz" },
         headers: { "HOST" => "accounts.inkreceipts.dev" }

    expect(response).to have_http_status(:created)
    parsed = JSON.parse(response.body)
    expect(parsed.fetch("consume_url")).to include("app.blkbxs.xyz")
    expect(SessionHandoff.count).to eq(1)
    expect(SessionHandoff.last.organization).to eq(organization)
    expect(SessionHandoff.last.workspace).to eq(workspace)
  end
end
