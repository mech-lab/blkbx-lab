module Api
  module V1
    module Blkbxs
      module LoanCases
        class ExportsController < BaseController
          before_action :ensure_blkbxs_workspace!

          def show
            return unless require_capability!("receipts:read")

            render_record(loan_case.export_packages.find(params[:id]))
          end

          def create
            return unless require_capability!("bundles:create")

            package = ::Blkbxs::Sprint::BuildExportPackage.call(
              loan_case: loan_case,
              actor: current_user,
              package_type: params[:package_type]
            )
            render_record(package, status: :created)
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
        end
      end
    end
  end
end
