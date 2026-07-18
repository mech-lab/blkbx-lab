require "rails_helper"

RSpec.describe Ink::HostedIssueReceipt do
  it "persists portable receipt metadata returned by the issuer service" do
    organization = create(:organization)
    workspace = create(:workspace, organization: organization, product_type: "mand8")
    receipt = Receipt.create!(
      organization: organization,
      workspace: workspace,
      schema_key: "mand8.risk_receipt.v1",
      schema_version: "1.0.0",
      workflow_kind: "insurability",
      body_json: { "schema" => "mand8.risk_receipt.v1", "decision" => "bind_with_controls" },
      domain_metadata: { "risk_class" => "medium" },
      issued_at: Time.utc(2026, 7, 18, 0, 0, 0)
    )

    allow(ENV).to receive(:[]).and_call_original
    allow(ENV).to receive(:fetch).and_call_original
    allow(ENV).to receive(:[]).with("INK_ISSUER_SERVICE_URL").and_return("http://issuer.test")
    allow(ENV).to receive(:[]).with("INK_ISSUER_SERVICE_TOKEN").and_return(nil)
    allow(ENV).to receive(:fetch).with("INK_ISSUER_SERVICE_URL").and_return("http://issuer.test")
    allow(ENV).to receive(:fetch).with("INK_ISSUER_SERVICE_TIMEOUT_SECONDS", 5).and_return(5)

    response = Net::HTTPOK.new("1.1", "200", "OK")
    allow(response).to receive(:body).and_return(
      JSON.generate(
        {
          receipt: {
            schema: "ink.receipt.v2",
            receipt_id: "urn:ink:receipt:rails:#{receipt.id}"
          },
          key_id: "platform-key-1",
          trust_registry_version: "2026-07-18.1",
          revocation_version: "2026-07-18.2",
          signer_request_id: "req-123"
        }
      )
    )
    http = instance_double(Net::HTTP)
    allow(http).to receive(:request).and_return(response)
    expect(Net::HTTP).to receive(:start).and_yield(http)

    described_class.call(receipt: receipt)

    receipt.reload
    expect(receipt.portable_receipt_json["schema"]).to eq("ink.receipt.v2")
    expect(receipt.signing_key_identifier).to eq("platform-key-1")
    expect(receipt.trust_registry_version).to eq("2026-07-18.1")
    expect(receipt.revocation_version).to eq("2026-07-18.2")
    expect(receipt.signer_request_id).to eq("req-123")
  end
end
