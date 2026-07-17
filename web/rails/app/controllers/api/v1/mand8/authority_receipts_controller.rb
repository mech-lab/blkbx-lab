module Api
  module V1
    module Mand8
      class AuthorityReceiptsController < WorkflowReceiptsController
        PRODUCT_TYPE = "mand8"
        WORKFLOW_KINDS = %w[authority].freeze
        self.workflow_service = ::Mand8::CreateAuthorityReceipt
      end
    end
  end
end
