module Api
  module V1
    module Mand8
      class VerifierArtifactsController < BaseController
        def show
          return render json: { error: "workspace product mismatch" }, status: :unprocessable_entity unless Current.workspace&.product_type == "mand8"

          authorize Current.workspace
          render json: ::Mand8::VerifierArtifacts.call(
            workspace: Current.workspace,
            case_id: params[:case_id],
            bundle_id: params[:bundle_id],
            receipt_id: params[:receipt_id]
          )
        rescue ActiveRecord::RecordNotFound
          render json: { error: "artifact context not found" }, status: :not_found
        end
      end
    end
  end
end
