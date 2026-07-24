module Api
  module V1
    module Blkbxs
      class VerifierArtifactsController < BaseController
        def show
          return render json: { error: "workspace product mismatch" }, status: :unprocessable_entity unless Current.workspace&.product_type == "blkbxs"
          return unless require_capability!("receipts:read")

          render json: ::Blkbxs::VerifierArtifacts.call(
            workspace: Current.workspace,
            business_process_id: params[:business_process_id],
            bundle_id: params[:bundle_id],
            receipt_id: params[:receipt_id]
          )
        rescue ActiveRecord::RecordNotFound => error
          render json: { error: error.message }, status: :not_found
        end
      end
    end
  end
end
