require "rails_helper"

RSpec.describe "BLKBXS Sprint Console", type: :request do
  def demo_fixture
    @demo_fixture ||= Blkbxs::DemoCatalog.fetch("smb_loan_demo")
  end

  def create_membership_workspace(product_type: "blkbxs")
    user = create(:user)
    organization = create(:organization)
    create(:membership, user: user, organization: organization, role: "owner")
    workspace = create(:workspace, organization: organization, product_type: product_type, slug: product_type)
    [user, organization, workspace]
  end

  def stub_successful_issuer
    allow(Ink::HostedIssueReceipt).to receive(:enabled?).and_return(true)
    allow(Ink::HostedIssueReceipt).to receive(:call) do |receipt:|
      receipt.update!(
        portable_receipt_json: {
          "schema" => "ink.receipt.v2",
          "receipt_id" => "urn:ink:receipt:rails:#{receipt.id}",
          "body_hash" => "signed-#{receipt.body_json.fetch('id')}"
        },
        signing_key_identifier: "test-issuer-key",
        trust_registry_version: "test-registry-v1",
        revocation_version: "test-revocations-v1",
        signer_request_id: "signer-request-#{receipt.id}"
      )
      receipt
    end
  end

  def seed_signed_case(user:, organization:, workspace:)
    stub_successful_issuer
    Blkbxs::Sprint::SeedSmb250kCase.call(
      organization: organization,
      workspace: workspace,
      actor: user,
      issue_events: true
    ).fetch(:loan_case)
  end

  before do
    SchemaCatalog.seed_defaults!
    WorkflowCatalog.seed_defaults!
  end

  it "creates the canonical SMB $250k sprint case without seeding unsigned events by default" do
    user, _organization, workspace = create_membership_workspace
    sign_in user

    expect do
      post "/api/v1/blkbxs/loan_cases",
           params: { workspace_id: workspace.id },
           headers: { "HOST" => "app.blkbxs.xyz" }
    end.to change(Blkbxs::LoanCase, :count).by(1)
      .and change(Blkbxs::EvidenceEvent, :count).by(0)
      .and change(Receipt, :count).by(0)

    expect(response).to have_http_status(:created)
    parsed = JSON.parse(response.body)
    expect(parsed.fetch("case_number")).to eq("BLKBXS-SMB-250K-001")
    expect(parsed.fetch("scenario_type")).to eq("smb_250k_conditional_approval")
    expect(parsed.fetch("borrower_name")).to eq("Sample Main Street Business LLC")
  end

  it "projects the generated fixture into eight signed evidence events" do
    stub_successful_issuer
    user, _organization, workspace = create_membership_workspace
    sign_in user

    expect do
      post "/api/v1/blkbxs/loan_cases",
           params: { workspace_id: workspace.id, seed_events: true },
           headers: { "HOST" => "app.blkbxs.xyz" }
    end.to change(Blkbxs::LoanCase, :count).by(1)
      .and change(Blkbxs::EvidenceEvent, :count).by(8)
      .and change(Receipt, :count).by(8)

    expect(response).to have_http_status(:created)
    loan_case = Blkbxs::LoanCase.find(JSON.parse(response.body).fetch("id"))
    expect(loan_case.evidence_events.pluck(:event_type)).to eq(demo_fixture.fetch("receipts").map { |body| body.dig("operation", "name") })
    expect(loan_case.receipts.all? { |receipt| receipt.portable_receipt.dig("schema") == "ink.receipt.v2" }).to eq(true)
    expect(loan_case.evidence_events.first.previous_event_hash).to be_nil
    expect(loan_case.evidence_events.second.previous_event_hash).to eq(loan_case.evidence_events.first.canonical_hash)
    expect(loan_case.status).to eq("conditional_approval_issued")
  end

  it "rolls back seeded case projection when hosted signing is unavailable" do
    allow(Ink::HostedIssueReceipt).to receive(:enabled?).and_return(false)
    user, _organization, workspace = create_membership_workspace
    sign_in user

    expect do
      post "/api/v1/blkbxs/loan_cases",
           params: { workspace_id: workspace.id, seed_events: true },
           headers: { "HOST" => "app.blkbxs.xyz" }
    end.to change(Blkbxs::LoanCase, :count).by(0)
      .and change(Blkbxs::EvidenceEvent, :count).by(0)
      .and change(Receipt, :count).by(0)

    expect(response).to have_http_status(:unprocessable_entity)
    expect(JSON.parse(response.body).fetch("error")).to include("portable ink.receipt.v2 signing is required")
  end

  it "rolls back evidence event creation when the issuer returns no portable receipt" do
    allow(Ink::HostedIssueReceipt).to receive(:enabled?).and_return(true)
    allow(Ink::HostedIssueReceipt).to receive(:call) { |receipt:| receipt }
    user, organization, workspace = create_membership_workspace
    loan_case = Blkbxs::Sprint::SeedSmb250kCase.call(organization: organization, workspace: workspace, actor: user).fetch(:loan_case)
    sign_in user

    expect do
      post "/api/v1/blkbxs/loan_cases/#{loan_case.id}/evidence_events",
           params: { workspace_id: workspace.id, body_json: demo_fixture.fetch("receipts").first },
           headers: { "HOST" => "app.blkbxs.xyz" }
    end.to change(Blkbxs::EvidenceEvent, :count).by(0)
      .and change(Receipt, :count).by(0)

    expect(response).to have_http_status(:unprocessable_entity)
    expect(JSON.parse(response.body).fetch("error")).to include("issuer did not return a receipt")
  end

  it "rejects sprint case creation in a non-BLKBXS workspace" do
    stub_successful_issuer
    user, _organization, workspace = create_membership_workspace(product_type: "ink")
    sign_in user

    post "/api/v1/blkbxs/loan_cases",
         params: { workspace_id: workspace.id, seed_events: true },
         headers: { "HOST" => "app.blkbxs.xyz" }

    expect(response).to have_http_status(:unprocessable_entity)
    expect(JSON.parse(response.body).fetch("error")).to eq("workspace product mismatch")
  end

  it "builds a sprint evidence bundle and final export package" do
    user, organization, workspace = create_membership_workspace
    loan_case = seed_signed_case(user: user, organization: organization, workspace: workspace)
    sign_in user

    expect do
      post "/api/v1/blkbxs/loan_cases/#{loan_case.id}/evidence_bundles",
           params: { workspace_id: workspace.id },
           headers: { "HOST" => "app.blkbxs.xyz" }
    end.to change(EvidenceBundle, :count).by(1)

    expect(response).to have_http_status(:created)
    bundle = EvidenceBundle.find(JSON.parse(response.body).fetch("id"))
    expect(bundle.manifest.fetch("case_number")).to eq("BLKBXS-SMB-250K-001")
    expect(bundle.manifest.fetch("verifier_handoff").fetch("available")).to eq(true)

    expect do
      post "/api/v1/blkbxs/loan_cases/#{loan_case.id}/exports",
           params: { workspace_id: workspace.id },
           headers: { "HOST" => "app.blkbxs.xyz" }
    end.to change(Blkbxs::ExportPackage, :count).by(1)

    expect(response).to have_http_status(:created)
    package = Blkbxs::ExportPackage.find(JSON.parse(response.body).fetch("id"))
    expect(File.exist?(package.file_path)).to eq(true)
    expect(package.manifest.fetch("files")).to include(
      "manifest.json",
      "loan_case.json",
      "receipt_graph.json",
      "claims_boundary_matrix.csv",
      "exception_register.csv",
      "reviewer_objections.csv",
      "verify_locally.md"
    )
  end

  it "runs sprint verification through the existing native verifier service boundary" do
    user, organization, workspace = create_membership_workspace
    loan_case = seed_signed_case(user: user, organization: organization, workspace: workspace)
    sign_in user

    allow(Ink::VerifyReceipt).to receive(:call) do |receipt:, verification_policy:, evidence_bundle:|
      VerificationRun.create!(
        organization: receipt.organization,
        workspace: receipt.workspace,
        receipt: receipt,
        verification_policy: verification_policy,
        evidence_bundle: evidence_bundle,
        status: "passed",
        report_json: { "status" => "passed" },
        verified_at: Time.current
      )
    end

    expect do
      post "/api/v1/blkbxs/loan_cases/#{loan_case.id}/verification_runs",
           params: { workspace_id: workspace.id },
           headers: { "HOST" => "app.blkbxs.xyz" }
    end.to change(VerificationRun, :count).by(1)

    expect(response).to have_http_status(:created)
    expect(loan_case.reload.status).to eq("verification_passed")
  end

  it "renders the seven reviewer cockpit screens" do
    user, organization, workspace = create_membership_workspace
    loan_case = seed_signed_case(user: user, organization: organization, workspace: workspace)
    sign_in user

    [
      "/blkbxs/sprint",
      "/blkbxs/sprint/loan_cases/#{loan_case.id}",
      "/blkbxs/sprint/loan_cases/#{loan_case.id}/timeline",
      "/blkbxs/sprint/loan_cases/#{loan_case.id}/receipt_graph",
      "/blkbxs/sprint/loan_cases/#{loan_case.id}/verification",
      "/blkbxs/sprint/loan_cases/#{loan_case.id}/objections",
      "/blkbxs/sprint/loan_cases/#{loan_case.id}/exports"
    ].each do |path|
      get path, headers: { "HOST" => "app.blkbxs.xyz" }
      expect(response).to have_http_status(:ok)
      expect(response.body).to include("BLKBXS Sprint Console")
    end
  end
end
