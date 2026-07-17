module Api
  module V1
    module Due
      class DefensibilityBundlesController < WorkflowBundlesController
        PRODUCT_TYPE = "due"
        BUNDLE_TYPES = %w[due_defensibility].freeze
        self.bundle_service = ::Due::BuildDefensibilityBundle
      end
    end
  end
end
