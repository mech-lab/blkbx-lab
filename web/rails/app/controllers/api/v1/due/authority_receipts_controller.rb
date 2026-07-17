module Api
  module V1
    module Due
      class AuthorityReceiptsController < WorkflowReceiptsController
        PRODUCT_TYPE = "due"
        WORKFLOW_KINDS = %w[authority].freeze
        self.workflow_service = ::Due::CreateAuthorityReceipt
      end
    end
  end
end
