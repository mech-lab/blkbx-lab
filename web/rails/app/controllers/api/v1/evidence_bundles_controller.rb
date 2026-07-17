module Api
  module V1
    class EvidenceBundlesController < BaseController
      def index
        return unless require_capability!("bundles:create")

        render_collection(Current.workspace.evidence_bundles.order(created_at: :desc))
      end

      def show
        return unless require_capability!("bundles:create")

        bundle = Current.workspace.evidence_bundles.find(params[:id])
        render_record(bundle)
      end

      def create
        return unless require_capability!("bundles:create")

        receipts = Current.workspace.receipts.where(id: params.require(:receipt_ids))
        bundle = Ink::BuildBundle.call(
          organization: Current.organization,
          workspace: Current.workspace,
          bundle_type: params.fetch(:bundle_type, "ink_generic"),
          title: params.fetch(:title, "Evidence bundle"),
          receipts: receipts,
          actor: current_user
        )
        render_record(bundle, status: :created)
      end
    end
  end
end
