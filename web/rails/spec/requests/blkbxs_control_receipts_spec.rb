require "rails_helper"

RSpec.describe "BLKBXS control receipts API", type: :request do
  it "creates a shared receipt inside a BLKBXS workspace" do
    user = create(:user)
    organization = create(:organization)
    create(:membership, user: user, organization: organization, role: "owner")
    create(:workspace, organization: organization, product_type: "ink", slug: "ink")
    create(:workspace, organization: organization, product_type: "blkbxs", slug: "blkbxs")

    sign_in user

    expect do
      post "/api/v1/blkbxs/control_receipts",
           params: {
             body_json: { action: "control_checked" },
             domain_metadata: { control_family: "aml" }
           },
           headers: { "HOST" => "app.blkbxs.xyz" }
    end.to change(Receipt, :count).by(1)

    expect(response).to have_http_status(:created)
    expect(Receipt.last.workspace.product_type).to eq("blkbxs")
    expect(Receipt.last.workflow_kind).to eq("control_execution")
  end
end
