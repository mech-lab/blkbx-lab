require "rails_helper"

RSpec.describe "MAND8 verifier artifacts", type: :request do
  def stub_hosted_issuer!
    allow(ENV).to receive(:[]).and_call_original
    allow(ENV).to receive(:fetch).and_call_original
    allow(ENV).to receive(:[]).with("INK_ISSUER_SERVICE_URL").and_return("http://issuer.test")
    allow(ENV).to receive(:[]).with("INK_ISSUER_SERVICE_TOKEN").and_return(nil)
    allow(ENV).to receive(:fetch).with("INK_ISSUER_SERVICE_URL").and_return("http://issuer.test")
    allow(ENV).to receive(:fetch).with("INK_ISSUER_SERVICE_TIMEOUT_SECONDS", 5).and_return(5)

    http = instance_double(Net::HTTP)
    allow(http).to receive(:request) do |request|
      payload = JSON.parse(request.body)
      response = Net::HTTPOK.new("1.1", "200", "OK")
      allow(response).to receive(:body).and_return(
        JSON.generate(
          {
            receipt: {
              schema: "ink.receipt.v2",
              receipt_id: payload.fetch("receipt_id"),
              action_id: payload.fetch("action_id")
            },
            manifest: {
              schema: "ink.manifest.v2",
              action_id: payload.fetch("action_id"),
              artifacts: []
            },
            key_id: "mand8-prod-key-1",
            trust_registry_version: "2026-07-18.1",
            revocation_version: "2026-07-18.2",
            signer_request_id: "signer-req-1"
          }
        )
      )
      response
    end
    allow(Net::HTTP).to receive(:start).and_yield(http)
  end

  def create_portable_case!(workspace:, case_id:)
    portable_receipt = Receipt.create!(
      organization: workspace.organization,
      workspace: workspace,
      schema_key: "ink.receipt.v2",
      schema_version: "2.0.0",
      workflow_kind: "portable_companion",
      external_id: "portable-#{case_id}",
      body_json: {
        "schema" => "ink.receipt.v2",
        "receipt_id" => "urn:ink:receipt:#{case_id}",
        "case_id" => case_id
      },
      domain_metadata: { "case_id" => case_id }
    )
    bundle = EvidenceBundle.create!(
      organization: workspace.organization,
      workspace: workspace,
      bundle_type: "portable_companion",
      title: "Portable verifier bundle",
      manifest: {
        "schema" => "ink.manifest.v2",
        "case_id" => case_id
      },
      sha256: "a" * 64
    )
    artifact = EvidenceArtifact.create!(
      organization: workspace.organization,
      workspace: workspace,
      receipt: portable_receipt,
      storage_key: "artifacts/#{workspace.id}/#{case_id}/ink_receipt.v2.json",
      sha256: "b" * 64,
      byte_size: 256,
      content_type: "application/json"
    )
    EvidenceBundleArtifact.create!(
      organization: workspace.organization,
      workspace: workspace,
      evidence_bundle: bundle,
      evidence_artifact: artifact
    )
    registry = TrustRegistry.create!(
      organization: workspace.organization,
      workspace: workspace,
      name: "Portable verifier registry",
      active: true,
      registry_json: {
        "schema" => "ink.trust-registry.v1",
        "issuers" => []
      }
    )
    create(
      :verification_policy,
      organization: workspace.organization,
      workspace: workspace,
      trust_registry: registry
    )

    { receipt: portable_receipt, bundle: bundle }
  end

  it "returns not found for seeded workspaces without portable verifier companions" do
    SchemaCatalog.seed_defaults!

    user = create(:user)
    organization = create(:organization)
    create(:membership, user: user, organization: organization, role: "owner")
    workspace = create(:workspace, organization: organization, product_type: "mand8")

    Mand8::SeedDemoWorkspace.call(workspace: workspace, scenario: "lloyds_cyber_happy_path", actor: user)
    bundle = workspace.evidence_bundles.first
    case_id = "case_mand8_lloyds_happy_001"

    sign_in user

    get "/api/v1/mand8/verifier_artifacts",
        params: { workspace_id: workspace.id },
        headers: { "HOST" => "app.mand8.ai" }
    expect(response).to have_http_status(:not_found)

    get "/api/v1/mand8/verifier_artifacts",
        params: { workspace_id: workspace.id, case_id: case_id },
        headers: { "HOST" => "app.mand8.ai" }
    expect(response).to have_http_status(:not_found)

    get "/api/v1/mand8/verifier_artifacts",
        params: { workspace_id: workspace.id, bundle_id: bundle.id },
        headers: { "HOST" => "app.mand8.ai" }
    expect(response).to have_http_status(:not_found)
  end

  it "returns portable verifier artifacts only when a real ink receipt is linked" do
    SchemaCatalog.seed_defaults!

    user = create(:user)
    organization = create(:organization)
    create(:membership, user: user, organization: organization, role: "owner")
    workspace = create(:workspace, organization: organization, product_type: "mand8")
    case_id = "case_portable_001"
    portable = create_portable_case!(workspace: workspace, case_id: case_id)

    sign_in user

    get "/api/v1/mand8/verifier_artifacts",
        params: { workspace_id: workspace.id },
        headers: { "HOST" => "app.mand8.ai" }
    expect(response).to have_http_status(:ok)
    workspace_payload = JSON.parse(response.body)
    expect(workspace_payload.dig("receipt", "schema")).to eq("ink.receipt.v2")
    expect(workspace_payload.dig("manifest", "schema")).to eq("ink.manifest.v2")
    expect(workspace_payload.dig("verification_policy", "schema")).to eq("ink.verify-policy.v1")
    expect(workspace_payload.dig("trust_registry", "schema")).to eq("ink.trust-registry.v1")
    expect(workspace_payload.dig("context", "receipt_id")).to eq(portable[:receipt].id)

    get "/api/v1/mand8/verifier_artifacts",
        params: { workspace_id: workspace.id, case_id: case_id },
        headers: { "HOST" => "app.mand8.ai" }
    expect(response).to have_http_status(:ok)
    case_payload = JSON.parse(response.body)
    expect(case_payload.dig("context", "case_id")).to eq(case_id)
    expect(case_payload.dig("context", "title")).to include(case_id)

    get "/api/v1/mand8/verifier_artifacts",
        params: { workspace_id: workspace.id, bundle_id: portable[:bundle].id },
        headers: { "HOST" => "app.mand8.ai" }
    expect(response).to have_http_status(:ok)
    bundle_payload = JSON.parse(response.body)
    expect(bundle_payload.dig("context", "bundle_id")).to eq(portable[:bundle].id)
    expect(bundle_payload.dig("receipt", "schema")).to eq("ink.receipt.v2")
  end

  it "exposes seeded canonical MAND8 verifier artifacts when the hosted issuer supplies a portable companion" do
    SchemaCatalog.seed_defaults!
    stub_hosted_issuer!

    user = create(:user)
    organization = create(:organization)
    create(:membership, user: user, organization: organization, role: "owner")
    workspace = create(:workspace, organization: organization, product_type: "mand8")

    seed_result = Mand8::SeedDemoWorkspace.call(workspace: workspace, scenario: "lloyds_incident_to_renewal", actor: user)
    expect(seed_result[:portable_companion_available]).to eq(true)

    bundle = workspace.evidence_bundles.find(seed_result[:bundle_id])
    expect(bundle.manifest.dig("verifier_handoff", "available")).to eq(true)

    sign_in user

    get "/api/v1/mand8/verifier_artifacts",
        params: { workspace_id: workspace.id, case_id: seed_result[:case_id] },
        headers: { "HOST" => "app.mand8.ai" }

    expect(response).to have_http_status(:ok)
    payload = JSON.parse(response.body)
    expect(payload.dig("receipt", "schema")).to eq("ink.receipt.v2")
    expect(payload.dig("manifest", "schema")).to eq("ink.manifest.v2")
    expect(payload.dig("verification_policy", "schema")).to eq("ink.verify-policy.v1")
    expect(payload.dig("context", "linked_receipt_schema")).to eq("mand8.risk_receipt.v1")
    expect(payload.dig("reviewer_packet", "schema")).to eq("mand8.reviewer_packet.v1")
    expect(payload.dig("reviewer_packet", "files", "manifest")).to eq("ink_manifest.v2.json")
    expect(payload.dig("reviewer_packet", "native_verify_command")).to include("--manifest ink_manifest.v2.json")
    expect(payload.dig("reviewer_packet", "vector_corpus")).to eq("test-vectors/ink-vectors.json")
  end

  it "rejects product mismatches and missing artifact contexts" do
    user = create(:user)
    organization = create(:organization)
    create(:membership, user: user, organization: organization, role: "owner")
    mand8_workspace = create(:workspace, organization: organization, product_type: "mand8")
    other_workspace = create(:workspace, organization: organization, product_type: "blkbxs")

    sign_in user

    get "/api/v1/mand8/verifier_artifacts",
        params: { workspace_id: other_workspace.id },
        headers: { "HOST" => "app.mand8.ai" }
    expect(response).to have_http_status(:unprocessable_entity)

    get "/api/v1/mand8/verifier_artifacts",
        params: { workspace_id: mand8_workspace.id, receipt_id: 999_999 },
        headers: { "HOST" => "app.mand8.ai" }
    expect(response).to have_http_status(:not_found)

    get "/api/v1/mand8/verifier_artifacts",
        params: { workspace_id: mand8_workspace.id },
        headers: { "HOST" => "app.mand8.ai" }
    expect(response).to have_http_status(:not_found)
  end
end
