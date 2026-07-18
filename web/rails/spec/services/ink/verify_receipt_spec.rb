require "rails_helper"

RSpec.describe Ink::VerifyReceipt do
  it "invokes the current ink receipt CLI command shape" do
    organization = create(:organization)
    workspace = create(:workspace, organization: organization, product_type: "mand8")
    receipt = Receipt.create!(
      organization: organization,
      workspace: workspace,
      schema_key: "mand8.risk_receipt.v1",
      schema_version: "1.0.0",
      body_json: {
        "schema" => "mand8.risk_receipt.v1",
        "case_id" => "case_verify_receipt_001"
      },
      domain_metadata: {}
    )
    verification_policy = create(
      :verification_policy,
      organization: organization,
      workspace: workspace
    )
    process = instance_double(Process::Status, success?: true)

    allow(AuditEvent).to receive(:record!)
    expect(Open3).to receive(:capture3).with(
      a_string_matching(%r{cargo run --quiet -p ink-cli -- receipt --receipt .* --policy .*})
    ).and_return(
      [
        JSON.generate({ "status" => "valid", "code" => "VALID_RECEIPT" }),
        "",
        process
      ]
    )

    run = described_class.call(receipt: receipt, verification_policy: verification_policy)

    expect(run.status).to eq("passed")
    expect(run.report_json["status"]).to eq("valid")
    expect(AuditEvent).to have_received(:record!).with(
      "receipt.verified",
      hash_including(auditable: run, organization: organization, workspace: workspace)
    )
  end
end
