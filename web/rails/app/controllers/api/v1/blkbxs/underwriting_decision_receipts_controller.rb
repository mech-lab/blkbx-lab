module Api
  module V1
    module Blkbxs
      class UnderwritingDecisionReceiptsController < WorkflowReceiptsController
        PRODUCT_TYPE = "blkbxs"
        WORKFLOW_KINDS = %w[underwriting_decision].freeze
        self.workflow_service = ::Blkbxs::CreateUnderwritingDecisionReceipt
      end
    end
  end
end
