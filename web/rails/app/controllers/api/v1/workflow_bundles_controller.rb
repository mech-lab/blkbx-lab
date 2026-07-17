module Api
  module V1
    class WorkflowBundlesController < BaseController
      class_attribute :bundle_service

      def index
        render_collection(Current.workspace.evidence_bundles.where(bundle_type: bundle_types).order(created_at: :desc))
      end

      def show
        bundle = Current.workspace.evidence_bundles.where(bundle_type: bundle_types).find(params[:id])
        render_record(bundle)
      end

      def create
        return unless ensure_product_match!
        return unless require_capability!("bundles:create")

        receipts = Current.workspace.receipts.where(id: params.require(:receipt_ids))
        bundle = bundle_service.call(
          organization: Current.organization,
          workspace: Current.workspace,
          actor: current_user,
          receipts: receipts,
          title: params[:title]
        )
        render_record(bundle, status: :created)
      rescue ArgumentError => error
        render json: { error: error.message }, status: :unprocessable_entity
      end

      private

      def bundle_types
        Array(self.class::BUNDLE_TYPES)
      end

      def ensure_product_match!
        return true if Current.workspace.product_type == self.class::PRODUCT_TYPE

        render json: { error: "workspace product mismatch" }, status: :unprocessable_entity
        false
      end
    end
  end
end
