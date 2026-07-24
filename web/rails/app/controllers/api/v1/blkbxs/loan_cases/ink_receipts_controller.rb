module Api
  module V1
    module Blkbxs
      module LoanCases
        class InkReceiptsController < BaseController
          before_action :ensure_blkbxs_workspace!

          def index
            return unless require_capability!("receipts:read")

            render json: loan_case.receipts.order(created_at: :asc).map do |receipt|
              receipt.as_json.merge(
                portable_receipt_available: receipt.portable_receipt.present?,
                evidence_event_id: receipt.blkbxs_evidence_events.find_by(loan_case: loan_case)&.id
              )
            end
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
        end
      end
    end
  end
end
