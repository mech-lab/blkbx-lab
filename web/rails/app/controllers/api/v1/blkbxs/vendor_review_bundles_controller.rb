module Api
  module V1
    module Blkbxs
      class VendorReviewBundlesController < WorkflowBundlesController
        PRODUCT_TYPE = "blkbxs"
        BUNDLE_TYPES = %w[blkbxs_bank_diligence].freeze
        self.bundle_service = ::Blkbxs::BuildVendorReviewBundle
      end
    end
  end
end
