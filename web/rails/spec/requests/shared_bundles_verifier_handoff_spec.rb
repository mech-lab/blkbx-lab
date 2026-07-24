require "rails_helper"

RSpec.describe "Shared bundles verifier handoff", type: :request do
  it "exposes MAND8 verifier handoff metadata on the public review surface" do
    SchemaCatalog.seed_defaults!

    user = create(:user)
    organization = create(:organization)
    create(:membership, user: user, organization: organization, role: "owner")
    workspace = create(:workspace, organization: organization, product_type: "mand8")

    Mand8::SeedDemoWorkspace.call(workspace: workspace, scenario: "lloyds_incident_to_renewal", actor: user)
    shared_bundle = workspace.shared_bundles.first
    reviewer = shared_bundle.review_request.reviewer
    access = PortalAccess.new(
      organization: organization,
      workspace: workspace,
      shared_bundle: shared_bundle,
      reviewer: reviewer,
      expires_at: 2.days.from_now
    )
    token = access.issue_secret!(prefix: "portal")
    access.save!

    get "/shared_bundles/#{shared_bundle.id}",
        params: { token: token },
        headers: { "HOST" => "app.mand8.ai" }

    expect(response).to have_http_status(:ok)
    parsed = JSON.parse(response.body)
    expect(parsed.dig("mand8", "case_summary", "case_id")).to eq("case_mand8_lloyds_incident_003")
    annotation = parsed.dig("mand8", "case_summary", "defensibility_annotation")
    expect(annotation.fetch("schema")).to eq("ink.actuarial_annotation.v1")
    expect(annotation.fetch("status")).to eq("research_unvalidated")
    expect(annotation.fetch("badge")).to eq("Research / unvalidated")
    expect(annotation.dig("engine", "profile")).to eq("mand8_case_v1")
    expect(annotation).not_to have_key("integrity")
    expect(annotation).not_to have_key("signature")
    expect(parsed.dig("mand8", "verifier_handoff", "product")).to eq("mand8")
    expect(parsed.dig("mand8", "verifier_handoff", "available")).to eq(false)
    expect(parsed.dig("mand8", "verifier_handoff", "reason_code")).to eq("PORTABLE_RECEIPT_MISSING")
    expect(parsed.dig("mand8", "verifier_handoff", "artifact_url")).to be_nil
    expect(parsed.dig("mand8", "verifier_handoff", "verify_path")).to be_nil
  end
end
