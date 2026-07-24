module Blkbxs
  module Sprint
    class DashboardsController < BaseController
      def show
        authorize Current.workspace
        @loan_cases = Current.workspace.blkbxs_loan_cases.recent
        @active_case = @loan_cases.first
        @graph_summary = ::Blkbxs::Sprint::GraphSummary.call(@active_case) if @active_case
      end
    end
  end
end
