module Api
  module V1
    module Due
      class PrivilegeReceiptsController < WorkflowReceiptsController
        PRODUCT_TYPE = "due"
        WORKFLOW_KINDS = %w[privilege].freeze
        self.workflow_service = ::Due::CreatePrivilegeReceipt
      end
    end
  end
end
