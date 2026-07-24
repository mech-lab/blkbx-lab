module Blkbxs
  module Sprint
    class BaseController < AuthenticatedController
      layout "blkbxs_sprint"

      before_action :ensure_blkbxs_workspace!

      private

      def ensure_blkbxs_workspace!
        return if Current.workspace&.product_type == "blkbxs"

        render plain: "BLKBXS workspace required", status: :unprocessable_entity
      end

      def loan_case
        @loan_case ||= Current.workspace.blkbxs_loan_cases.find(params[:id] || params[:loan_case_id])
      end

      def graph_summary
        @graph_summary ||= ::Blkbxs::Sprint::GraphSummary.call(loan_case)
      end
    end
  end
end
