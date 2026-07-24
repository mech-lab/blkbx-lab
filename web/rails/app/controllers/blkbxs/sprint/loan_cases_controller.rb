module Blkbxs
  module Sprint
    class LoanCasesController < BaseController
      before_action :set_case_context, only: %i[show timeline receipt_graph verification objections exports]

      def index
        authorize Current.workspace
        @loan_cases = Current.workspace.blkbxs_loan_cases.recent
      end

      def show; end

      def timeline; end

      def receipt_graph; end

      def verification
        @verification_runs = VerificationRun.where(receipt: @loan_case.receipts).recent
        @exceptions = ::Blkbxs::Sprint::BuildExceptionRegister.call(@loan_case)
      end

      def objections
        @objections = @loan_case.reviewer_objections.order(:function, :created_at)
      end

      def exports
        @export_packages = @loan_case.export_packages.order(created_at: :desc)
        @bundles = Current.workspace.evidence_bundles.where(bundle_type: "blkbxs_ubr_graph").select do |bundle|
          bundle.manifest["loan_case_id"] == @loan_case.id || bundle.manifest["case_number"] == @loan_case.case_number
        end
      end

      private

      def set_case_context
        authorize Current.workspace
        @loan_case = loan_case
        @graph_summary = graph_summary
        @events = @loan_case.evidence_events.ordered
        @claims = ::Blkbxs::Sprint::BuildClaimsBoundaryMatrix.call(@loan_case)
      end
    end
  end
end
