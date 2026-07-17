module Rack
  class DomainProductResolver
    def initialize(app)
      @app = app
    end

    def call(env)
      request = ActionDispatch::Request.new(env)
      Current.reset
      Current.product = ProductCatalog.product_for_host(request.host)
      Current.brand = ProductCatalog.brand_for(Current.product)
      Current.identity_host = ProductCatalog.identity_host?(request.host)
      @app.call(env)
    ensure
      Current.reset
    end
  end
end
