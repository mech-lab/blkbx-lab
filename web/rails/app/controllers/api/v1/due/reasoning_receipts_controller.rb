module Api
  module V1
    module Due
      class ReasoningReceiptsController < WorkflowReceiptsController
        PRODUCT_TYPE = "due"
        WORKFLOW_KINDS = %w[reasoning].freeze
        self.workflow_service = ::Due::CreateReasoningReceipt
      end
    end
  end
end
