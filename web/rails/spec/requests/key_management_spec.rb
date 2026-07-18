require "rails_helper"

RSpec.describe "Key management", type: :request do
  it "requires two distinct approver roles before activation and publication" do
    owner = create(:user)
    admin = create(:user)
    organization = create(:organization)
    create(:membership, user: owner, organization: organization, role: "owner")
    create(:membership, user: admin, organization: organization, role: "administrator")
    workspace = create(:workspace, organization: organization, product_type: "ink")
    retired_key = create(
      :signing_key,
      organization: organization,
      workspace: workspace,
      key_identifier: "receipt-old",
      state: "active",
      usage: "receipt_signing"
    )
    trust_authority = create(
      :signing_key,
      organization: organization,
      workspace: workspace,
      key_identifier: "trust-authority",
      usage: "trust_publication",
      state: "active"
    )

    sign_in owner

    post "/api/v1/signing_keys",
         params: {
           signing_key: {
             key_identifier: "receipt-next",
             public_key: Base64.urlsafe_encode64("\x02" * 32, padding: false),
             key_type: "Ed25519",
             usage: "receipt_signing",
             custody_kind: "cloud_kms_hsm"
           }
         }
    expect(response).to have_http_status(:created)
    new_key = SigningKey.find(JSON.parse(response.body).fetch("id"))

    post "/api/v1/key_ceremonies",
         params: {
           key_ceremony: {
             signing_key_id: new_key.id,
             ceremony_kind: "rotate_key"
           }
         }
    expect(response).to have_http_status(:created)
    ceremony_id = JSON.parse(response.body).fetch("id")

    post "/api/v1/key_ceremonies/#{ceremony_id}/approve", params: { note: "owner approved" }
    expect(response).to have_http_status(:ok)
    expect(KeyCeremony.find(ceremony_id).state).to eq("pending_approval")

    sign_in admin
    post "/api/v1/key_ceremonies/#{ceremony_id}/approve", params: { note: "admin approved" }
    expect(response).to have_http_status(:ok)
    expect(KeyCeremony.find(ceremony_id).state).to eq("approved")

    post "/api/v1/key_ceremonies/#{ceremony_id}/activate"
    expect(response).to have_http_status(:ok)
    expect(new_key.reload.state).to eq("active")
    expect(retired_key.reload.state).to eq("retired")

    post "/api/v1/key_ceremonies/#{ceremony_id}/publish",
         params: {
           trust_publication: {
             artifact_kind: "trust_registry",
             version: "2026-07-18.1"
           }
         }
    expect(response).to have_http_status(:ok)
    publication = TrustPublication.last
    expect(publication.signing_key).to eq(new_key)
    expect(publication.state).to eq("pending_signature")
    expect(publication.artifact_json.dig("trust_authorities", 0, "key_id")).to eq(trust_authority.key_identifier)

    get "/api/v1/trust_publications/current", params: { artifact_kind: "trust_registry" }
    expect(response).to have_http_status(:ok)
    expect(JSON.parse(response.body).fetch("version")).to eq("2026-07-18.1")
  end
end
