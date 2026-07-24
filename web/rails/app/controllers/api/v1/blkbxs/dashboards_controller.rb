module Api
  module V1
    module Blkbxs
      class DashboardsController < BaseController
        def show
          return render json: { error: "workspace product mismatch" }, status: :unprocessable_entity unless Current.workspace&.product_type == "blkbxs"

          authorize Current.workspace
          render json: ::Blkbxs::WorkspaceSnapshot.call(Current.workspace)
        end
      end
    end
  end
end

