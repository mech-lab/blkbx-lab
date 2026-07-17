require "spec_helper"
require "action_dispatch"
require "active_support/current_attributes"
require "rack/mock"

require_relative "../../app/models/current"
require_relative "../../app/services/product_catalog"
require_relative "../../lib/rack/domain_product_resolver"

RSpec.describe Rack::DomainProductResolver do
  it "sets product context from the request host and resets afterward" do
    downstream = lambda do |_env|
      [200, { "content-type" => "text/plain" }, ["#{Current.brand}|#{Current.product}|#{Current.identity_host}"]]
    end

    status, _headers, body = described_class.new(downstream).call(
      Rack::MockRequest.env_for("/", "HTTP_HOST" => "app.blkbxs.xyz")
    )

    expect(status).to eq(200)
    expect(body.each.to_a.join).to eq("BLKBXS|blkbxs|false")
    expect(Current.product).to be_nil
    expect(Current.brand).to be_nil
    expect(Current.identity_host).to be_nil
  end
end
