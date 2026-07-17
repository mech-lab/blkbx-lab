module Api
  module V1
    module Due
      class MatterExportsController < BaseController
        def create
          return unless ensure_product_match!

          customer_project = Current.workspace.customer_projects.find(params.require(:customer_project_id))
          receipts = Current.workspace.receipts.where(id: params.require(:receipt_ids))
          result = ::Due::ExportMatter.call(
            organization: Current.organization,
            workspace: Current.workspace,
            actor: current_user,
            customer_project: customer_project,
            receipts: receipts
          )
          render json: {
            customer_project: result[:customer_project].as_json,
            evidence_bundle: result[:evidence_bundle].as_json
          }, status: :created
        end

        private

        def ensure_product_match!
          return true if Current.workspace.product_type == "due"

          render json: { error: "workspace product mismatch" }, status: :unprocessable_entity
          false
        end
      end
    end
  end
end
