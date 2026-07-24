module Api
  module V1
    module Blkbxs
      module LoanCases
        class VerificationRunsController < BaseController
          before_action :ensure_blkbxs_workspace!

          def index
            return unless require_capability!("receipts:read")

            render json: runs.map(&:as_json)
          end

          def show
            return unless require_capability!("receipts:read")

            render_record(runs.find(params[:id]))
          end

          def create
            return unless require_capability!("verifications:create")

            run = ::Blkbxs::Sprint::RunVerification.call(loan_case: loan_case)
            render_record(run, status: :created)
          rescue ArgumentError => error
            render json: { error: error.message }, status: :unprocessable_entity
          end

          private

          def ensure_blkbxs_workspace!
            return true if Current.workspace&.product_type == "blkbxs"

            render json: { error: "workspace product mismatch" }, status: :unprocessable_entity
            false
          end

          def loan_case
            @loan_case ||= Current.workspace.blkbxs_loan_cases.find(params[:loan_case_id])
          end

          def runs
            @runs ||= VerificationRun.where(receipt: loan_case.receipts).recent
          end
        end
      end
    end
  end
end
