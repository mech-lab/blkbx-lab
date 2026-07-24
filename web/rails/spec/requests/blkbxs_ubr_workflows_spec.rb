require "rails_helper"

RSpec.describe "BLKBXS UBR workflows", type: :request do
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

  def create_signed_ubr_receipt(organization:, workspace:, body:, portable_receipt: true, external_id: nil)
    normalized = Blkbxs::ReceiptContract.ubr_event(body: body)
    attributes = {
      organization: organization,
      workspace: workspace,
      schema_key: "blkbxs.ubr.receipt.v1",
      schema_version: "1.0.0",
      workflow_kind: "ubr_event",
      external_id: external_id || normalized.fetch("id"),
      body_json: normalized,
      domain_metadata: Blkbxs::ReceiptContract.domain_metadata_for(body: normalized),
      issued_at: normalized.fetch("issued_at"),
      storage_key: "receipts/#{normalized.fetch('id')}.ink",
      sha256: Digest::SHA256.hexdigest(JSON.generate(normalized)),
      signing_key_identifier: "test-issuer-key"
    }
    if portable_receipt
      attributes[:portable_receipt_json] = {
        "schema" => "ink.receipt.v2",
        "receipt_id" => "urn:ink:test:#{normalized.fetch('id')}"
      }
    end
    Receipt.create!(attributes)
  end

  before do
    SchemaCatalog.seed_defaults!
    WorkflowCatalog.seed_defaults!
  end

  it "creates a UBR receipt only when a portable ink receipt is issued" do
    stub_successful_issuer
    user, _organization, workspace = create_membership_workspace
    sign_in user

    expect do
      post "/api/v1/blkbxs/ubr_receipts",
           params: {
             workspace_id: workspace.id,
             body_json: demo_fixture.fetch("receipts").first,
             domain_metadata: { source: "request_spec" }
           },
           headers: { "HOST" => "app.blkbxs.xyz" }
    end.to change(Receipt, :count).by(1)

    expect(response).to have_http_status(:created)
    parsed = JSON.parse(response.body)
    expect(parsed.fetch("schema_key")).to eq("blkbxs.ubr.receipt.v1")
    expect(parsed.fetch("workflow_kind")).to eq("ubr_event")
    expect(parsed.dig("portable_receipt_json", "schema")).to eq("ink.receipt.v2")
    expect(parsed.dig("portable_receipt", "available")).to eq(true)
    expect(parsed.dig("domain_metadata", "business_process_id")).to eq("urn:bank-process:loan-origination:APP-2026-00019381")
  end

  it "rolls back UBR receipt creation when portable signing is unavailable" do
    allow(Ink::HostedIssueReceipt).to receive(:enabled?).and_return(false)
    user, _organization, workspace = create_membership_workspace
    sign_in user

    expect do
      post "/api/v1/blkbxs/ubr_receipts",
           params: {
             workspace_id: workspace.id,
             body_json: demo_fixture.fetch("receipts").first
           },
           headers: { "HOST" => "app.blkbxs.xyz" }
    end.not_to change(Receipt, :count)

    expect(response).to have_http_status(:unprocessable_entity)
    expect(JSON.parse(response.body).fetch("error")).to include("portable ink.receipt.v2 signing is required")
  end

  it "rolls back UBR receipt creation when the issuer service fails" do
    allow(Ink::HostedIssueReceipt).to receive(:enabled?).and_return(true)
    allow(Ink::HostedIssueReceipt).to receive(:call).and_raise(StandardError, "issuer offline")
    user, _organization, workspace = create_membership_workspace
    sign_in user

    expect do
      post "/api/v1/blkbxs/ubr_receipts",
           params: {
             workspace_id: workspace.id,
             body_json: demo_fixture.fetch("receipts").first
           },
           headers: { "HOST" => "app.blkbxs.xyz" }
    end.not_to change(Receipt, :count)

    expect(response).to have_http_status(:unprocessable_entity)
    expect(JSON.parse(response.body).fetch("error")).to include("portable ink.receipt.v2 signing failed: issuer offline")
  end

  it "rolls back UBR receipt creation when the issuer returns no portable receipt" do
    allow(Ink::HostedIssueReceipt).to receive(:enabled?).and_return(true)
    allow(Ink::HostedIssueReceipt).to receive(:call) { |receipt:| receipt }
    user, _organization, workspace = create_membership_workspace
    sign_in user

    expect do
      post "/api/v1/blkbxs/ubr_receipts",
           params: {
             workspace_id: workspace.id,
             body_json: demo_fixture.fetch("receipts").first
           },
           headers: { "HOST" => "app.blkbxs.xyz" }
    end.not_to change(Receipt, :count)

    expect(response).to have_http_status(:unprocessable_entity)
    expect(JSON.parse(response.body).fetch("error")).to include("issuer did not return a receipt")
  end

  it "rejects UBR receipt creation in a non-BLKBXS workspace" do
    stub_successful_issuer
    user, _organization, workspace = create_membership_workspace(product_type: "ink")
    sign_in user

    post "/api/v1/blkbxs/ubr_receipts",
         params: {
           workspace_id: workspace.id,
           body_json: demo_fixture.fetch("receipts").first
         },
         headers: { "HOST" => "app.blkbxs.xyz" }

    expect(response).to have_http_status(:unprocessable_entity)
    expect(JSON.parse(response.body).fetch("error")).to eq("workspace product mismatch")
  end

  it "builds a same-process UBR graph bundle and rejects mixed-process receipts" do
    user, organization, workspace = create_membership_workspace
    receipts = demo_fixture.fetch("receipts").map do |body|
      create_signed_ubr_receipt(organization: organization, workspace: workspace, body: body)
    end
    sign_in user

    post "/api/v1/blkbxs/ubr_bundles",
         params: {
           workspace_id: workspace.id,
           title: "SMB loan UBR graph",
           receipt_ids: receipts.map(&:id),
           evidence_manifest: demo_fixture.fetch("evidence_manifest"),
           verifier_report: demo_fixture.fetch("verifier_report")
         },
         headers: { "HOST" => "app.blkbxs.xyz" }

    expect(response).to have_http_status(:created)
    bundle = JSON.parse(response.body)
    expect(bundle.dig("manifest", "business_process_id")).to eq("urn:bank-process:loan-origination:APP-2026-00019381")
    expect(bundle.dig("manifest", "graph_validation", "valid")).to eq(true)
    expect(bundle.dig("manifest", "evidence_summary", "available_to_verifier")).to eq(6)
    expect(bundle.dig("manifest", "evidence_summary", "committed_only")).to eq(2)
    expect(bundle.dig("manifest", "ai_boundary_summary", "valid")).to eq(true)
    expect(bundle.dig("manifest", "verifier_handoff", "available")).to eq(true)

    other_body = Marshal.load(Marshal.dump(demo_fixture.fetch("receipts").last))
    other_body["operation"]["business_process_id"] = "urn:bank-process:loan-origination:OTHER"
    other = create_signed_ubr_receipt(organization: organization, workspace: workspace, body: other_body)

    expect do
      post "/api/v1/blkbxs/ubr_bundles",
           params: {
             workspace_id: workspace.id,
             title: "Invalid mixed graph",
             receipt_ids: [receipts.first.id, other.id],
             evidence_manifest: demo_fixture.fetch("evidence_manifest")
           },
           headers: { "HOST" => "app.blkbxs.xyz" }
    end.not_to change(EvidenceBundle, :count)

    expect(response).to have_http_status(:unprocessable_entity)
    expect(JSON.parse(response.body).fetch("error")).to include("BLKBXS UBR graph is invalid")
  end

  it "rejects duplicate UBR receipt ids and unsigned receipts in graph bundles" do
    user, organization, workspace = create_membership_workspace
    first = create_signed_ubr_receipt(organization: organization, workspace: workspace, body: demo_fixture.fetch("receipts").first)
    duplicate_body = Marshal.load(Marshal.dump(demo_fixture.fetch("receipts").second))
    duplicate_body["id"] = first.body_json.fetch("id")
    duplicate = create_signed_ubr_receipt(
      organization: organization,
      workspace: workspace,
      body: duplicate_body,
      external_id: "#{duplicate_body.fetch('id')}:duplicate"
    )
    unsigned = create_signed_ubr_receipt(
      organization: organization,
      workspace: workspace,
      body: demo_fixture.fetch("receipts").third,
      portable_receipt: false
    )
    sign_in user

    expect do
      post "/api/v1/blkbxs/ubr_bundles",
           params: {
             workspace_id: workspace.id,
             title: "Invalid duplicate graph",
             receipt_ids: [first.id, duplicate.id],
             evidence_manifest: demo_fixture.fetch("evidence_manifest")
           },
           headers: { "HOST" => "app.blkbxs.xyz" }
    end.not_to change(EvidenceBundle, :count)

    expect(response).to have_http_status(:unprocessable_entity)
    expect(JSON.parse(response.body).fetch("error")).to include("duplicate_receipt_id")

    expect do
      post "/api/v1/blkbxs/ubr_bundles",
           params: {
             workspace_id: workspace.id,
             title: "Invalid unsigned graph",
             receipt_ids: [first.id, unsigned.id],
             evidence_manifest: demo_fixture.fetch("evidence_manifest")
           },
           headers: { "HOST" => "app.blkbxs.xyz" }
    end.not_to change(EvidenceBundle, :count)

    expect(response).to have_http_status(:unprocessable_entity)
    expect(JSON.parse(response.body).fetch("error")).to include("linked ink.receipt.v2 portable receipt")
  end

  it "rejects verifier artifact handoff when any selected UBR receipt is unsigned" do
    user, organization, workspace = create_membership_workspace
    create_signed_ubr_receipt(
      organization: organization,
      workspace: workspace,
      body: demo_fixture.fetch("receipts").first,
      portable_receipt: false
    )
    sign_in user

    get "/api/v1/blkbxs/verifier_artifacts",
        params: {
          workspace_id: workspace.id,
          business_process_id: "urn:bank-process:loan-origination:APP-2026-00019381"
        },
        headers: { "HOST" => "app.blkbxs.xyz" }

    expect(response).to have_http_status(:not_found)
    expect(JSON.parse(response.body).fetch("error")).to include("No linked portable ink.receipt.v2 found")
  end

  it "adds BLKBXS graph context to the shared reviewer portal" do
    user, organization, workspace = create_membership_workspace
    receipts = demo_fixture.fetch("receipts").map do |body|
      create_signed_ubr_receipt(organization: organization, workspace: workspace, body: body)
    end
    bundle = Blkbxs::BuildUbrBundle.call(
      organization: organization,
      workspace: workspace,
      actor: user,
      receipts: receipts,
      title: "SMB loan UBR graph",
      evidence_manifest: demo_fixture.fetch("evidence_manifest"),
      verifier_report: demo_fixture.fetch("verifier_report")
    )
    review_request, shared_bundle = Workflows::CreateReviewRequest.call(
      organization: organization,
      workspace: workspace,
      evidence_bundle: bundle,
      title: "Bank credit review",
      reviewer_email: "credit.reviewer@blkbxs.example",
      reviewer_name: "Credit Reviewer",
      reviewer_role: "bank_credit_review",
      actor: user
    )
    access = PortalAccess.new(
      organization: organization,
      workspace: workspace,
      shared_bundle: shared_bundle,
      reviewer: review_request.reviewer,
      expires_at: 2.days.from_now
    )
    token = access.issue_secret!(prefix: "portal")
    access.save!

    get "/shared_bundles/#{shared_bundle.id}",
        params: { token: token },
        headers: { "HOST" => "app.blkbxs.xyz" }

    expect(response).to have_http_status(:ok)
    parsed = JSON.parse(response.body)
    expect(parsed.dig("blkbxs", "graph_summary", "business_process_id")).to eq("urn:bank-process:loan-origination:APP-2026-00019381")
    expect(parsed.dig("blkbxs", "graph_summary", "graph_valid")).to eq(true)
    expect(parsed.dig("blkbxs", "graph_summary", "decision_summary", "status")).to eq("conditionally_approved")
    expect(parsed.dig("blkbxs", "verifier_handoff", "available")).to eq(true)
  end
end
