module Api
  module V1
    class WorkflowReceiptsController < BaseController
      class_attribute :workflow_service

      def index
        render_collection(Current.workspace.receipts.where(workflow_kind: workflow_kinds).order(created_at: :desc))
      end

      def show
        receipt = Current.workspace.receipts.where(workflow_kind: workflow_kinds).find(params[:id])
        render_record(receipt)
      end

      def create
        return unless ensure_product_match!
        return unless require_capability!("receipts:write")

        _workflow_run, receipt = workflow_service.call(
          organization: Current.organization,
          workspace: Current.workspace,
          actor: current_user,
          body: workflow_params[:body_json] || {},
          domain_metadata: workflow_params[:domain_metadata] || {}
        )
        render_record(receipt, status: :created)
      end

      private

      def workflow_kinds
        Array(self.class::WORKFLOW_KINDS)
      end

      def workflow_params
        params.permit(body_json: {}, domain_metadata: {})
      end

      def ensure_product_match!
        return true if Current.workspace.product_type == self.class::PRODUCT_TYPE

        render json: { error: "workspace product mismatch" }, status: :unprocessable_entity
        false
      end
    end
  end
end
