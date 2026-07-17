require "spec_helper"
require_relative "../../app/services/product_catalog"

RSpec.describe ProductCatalog do
  it "maps branded hosts to product surfaces" do
    expect(described_class.product_for_host("app.blkbxs.xyz")).to eq(:blkbxs)
    expect(described_class.product_for_host("app.mand8.ai")).to eq(:mand8)
    expect(described_class.product_for_host("app.due.example")).to eq(:due)
    expect(described_class.product_for_host("app.inkreceipts.dev")).to eq(:ink)
  end
end
