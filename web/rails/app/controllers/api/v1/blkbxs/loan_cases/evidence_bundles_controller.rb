module Api
  module V1
    module Blkbxs
      module LoanCases
        class EvidenceBundlesController < BaseController
          before_action :ensure_blkbxs_workspace!

          def index
            return unless require_capability!("receipts:read")

            render json: bundles.map(&:as_json)
          end

          def show
            return unless require_capability!("receipts:read")

            bundle = bundles.find { |record| record.id == params[:id].to_i }
            raise ActiveRecord::RecordNotFound, "BLKBXS sprint evidence bundle not found" unless bundle

            render_record(bundle)
          end

          def create
            return unless require_capability!("bundles:create")

            bundle = ::Blkbxs::Sprint::BuildEvidenceBundle.call(
              loan_case: loan_case,
              actor: current_user,
              title: params[:title]
            )
            render_record(bundle, status: :created)
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

          def bundles
            @bundles ||= Current.workspace.evidence_bundles.where(bundle_type: "blkbxs_ubr_graph").select do |bundle|
              bundle.manifest["loan_case_id"] == loan_case.id || bundle.manifest["case_number"] == loan_case.case_number
            end
          end
        end
      end
    end
  end
end
