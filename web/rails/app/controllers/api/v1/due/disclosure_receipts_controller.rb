module Api
  module V1
    module Due
      class DisclosureReceiptsController < WorkflowReceiptsController
        PRODUCT_TYPE = "due"
        WORKFLOW_KINDS = %w[disclosure].freeze
        self.workflow_service = ::Due::CreateDisclosureReceipt
      end
    end
  end
end
