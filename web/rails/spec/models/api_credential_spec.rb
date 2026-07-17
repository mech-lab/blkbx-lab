require "rails_helper"

RSpec.describe ApiCredential, type: :model do
  it "issues and authenticates a secret once stored" do
    organization = create(:organization)
    workspace = create(:workspace, organization: organization, product_type: "ink")
    credential = described_class.new(
      organization: organization,
      workspace: workspace,
      name: "Primary",
      capabilities: %w[receipts:write]
    )

    token = credential.issue_secret!(prefix: "cred")
    credential.save!

    _identifier, secret = token.split(".", 2)
    expect(credential.authenticate_secret(secret)).to be(true)
    expect(credential.serializable_hash.keys).not_to include("secret_hash")
  end
end
