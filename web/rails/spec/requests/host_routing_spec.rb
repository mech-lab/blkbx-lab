require "rails_helper"

RSpec.describe "Host-based product routing", type: :request do
  it "renders BLKBXS branding on the BLKBXS host" do
    get "/", headers: { "HOST" => "app.blkbxs.xyz" }

    expect(response).to have_http_status(:ok)
    expect(response.body).to include("BLKBXS")
  end
end
