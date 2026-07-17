module Api
  module V1
    module Mand8
      class DashboardsController < BaseController
        def show
          return render json: { error: "workspace product mismatch" }, status: :unprocessable_entity unless Current.workspace&.product_type == "mand8"

          authorize Current.workspace
          render json: ::Mand8::WorkspaceSnapshot.call(Current.workspace)
        end
      end
    end
  end
end
