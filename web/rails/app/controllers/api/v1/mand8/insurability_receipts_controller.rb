module Api
  module V1
    module Mand8
      class InsurabilityReceiptsController < WorkflowReceiptsController
        PRODUCT_TYPE = "mand8"
        WORKFLOW_KINDS = %w[insurability].freeze
        self.workflow_service = ::Mand8::CreateInsurabilityReceipt
      end
    end
  end
end
