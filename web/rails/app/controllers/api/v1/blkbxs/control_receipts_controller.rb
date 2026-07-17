module Api
  module V1
    module Blkbxs
      class ControlReceiptsController < WorkflowReceiptsController
        PRODUCT_TYPE = "blkbxs"
        WORKFLOW_KINDS = %w[control_execution].freeze
        self.workflow_service = ::Blkbxs::CreateControlReceipt
      end
    end
  end
end
