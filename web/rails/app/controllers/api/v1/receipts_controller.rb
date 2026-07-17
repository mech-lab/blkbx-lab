module Api
  module V1
    class ReceiptsController < BaseController
      def index
        return unless require_capability!("receipts:read")

        render_collection(Current.workspace.receipts.order(created_at: :desc))
      end

      def show
        return unless require_capability!("receipts:read")

        receipt = Current.workspace.receipts.find(params[:id])
        authorize receipt unless Current.api_credential
        render_record(receipt)
      end

      def create
        return unless require_capability!("receipts:write")

        workspace = Current.workspace || Workspace.find(params.require(:workspace_id))
        organization = Current.organization || workspace.organization
        authorize Receipt.new(organization: organization, workspace: workspace) unless Current.api_credential

        _workflow_run, receipt = Ink::IssueReceipt.call(
          organization: organization,
          workspace: workspace,
          actor: current_user,
          workflow_kind: receipt_params[:workflow_kind].presence || "ink_generic",
          schema_key: receipt_params[:schema_key],
          schema_version: receipt_params[:schema_version],
          external_id: receipt_params[:external_id],
          body: receipt_params[:body_json] || {},
          domain_metadata: receipt_params[:domain_metadata] || {}
        )

        render_record(receipt, status: :created)
      end

      private

      def receipt_params
        params.require(:receipt).permit(:workspace_id, :schema_key, :schema_version, :workflow_kind, :external_id, body_json: {}, domain_metadata: {})
      end
    end
  end
end
