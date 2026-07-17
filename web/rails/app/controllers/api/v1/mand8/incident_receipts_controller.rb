module Api
  module V1
    module Mand8
      class IncidentReceiptsController < WorkflowReceiptsController
        PRODUCT_TYPE = "mand8"
        WORKFLOW_KINDS = %w[incident].freeze
        self.workflow_service = ::Mand8::CreateIncidentReceipt
      end
    end
  end
end
