module Api
  module V1
    module Blkbxs
      class LoanCasesController < BaseController
        before_action :ensure_blkbxs_workspace!

        def index
          return unless require_capability!("receipts:read")

          render json: Current.workspace.blkbxs_loan_cases.recent.map { |loan_case| loan_case_payload(loan_case) }
        end

        def show
          return unless require_capability!("receipts:read")

          render json: loan_case_payload(loan_case)
        end

        def create
          return unless require_capability!("receipts:write")

          result = ::Blkbxs::Sprint::SeedSmb250kCase.call(
            organization: Current.organization,
            workspace: Current.workspace,
            actor: current_user,
            issue_events: ActiveModel::Type::Boolean.new.cast(params[:seed_events])
          )
          render json: loan_case_payload(result.fetch(:loan_case)).merge(fixture: result.fetch(:fixture)), status: :created
        rescue Workflows::CreateReceipt::PortableReceiptRequiredError, ArgumentError => error
          render json: { error: error.message }, status: :unprocessable_entity
        end

        private

        def ensure_blkbxs_workspace!
          return true if Current.workspace&.product_type == "blkbxs"

          render json: { error: "workspace product mismatch" }, status: :unprocessable_entity
          false
        end

        def loan_case
          @loan_case ||= Current.workspace.blkbxs_loan_cases.find(params[:id])
        end

        def loan_case_payload(record)
          record.as_json.merge(
            sprint_engagement: record.sprint_engagement.as_json,
            graph_summary: ::Blkbxs::Sprint::GraphSummary.call(record)
          )
        end
      end
    end
  end
end
