module Api
  module V1
    module Mand8
      class RenewalBundlesController < WorkflowBundlesController
        PRODUCT_TYPE = "mand8"
        BUNDLE_TYPES = %w[mand8_renewal].freeze
        self.bundle_service = ::Mand8::BuildRenewalBundle
      end
    end
  end
end
