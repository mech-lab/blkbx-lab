module Api
  module V1
    module Blkbxs
      class UbrBundlesController < WorkflowBundlesController
        PRODUCT_TYPE = "blkbxs"
        BUNDLE_TYPES = %w[blkbxs_ubr_graph].freeze
        self.bundle_service = ::Blkbxs::BuildUbrBundle

        def create
          return unless ensure_product_match!
          return unless require_capability!("bundles:create")

          receipts = Current.workspace.receipts.where(id: params.require(:receipt_ids))
          bundle = bundle_service.call(
            organization: Current.organization,
            workspace: Current.workspace,
            actor: current_user,
            receipts: receipts,
            title: params[:title],
            evidence_manifest: json_param(:evidence_manifest),
            verifier_report: json_param(:verifier_report)
          )
          render_record(bundle, status: :created)
        rescue ArgumentError => error
          render json: { error: error.message }, status: :unprocessable_entity
        end

        private

        def json_param(key)
          value = params[key]
          return nil if value.blank?
          return value.to_unsafe_h if value.respond_to?(:to_unsafe_h)
          return value.to_h if value.respond_to?(:to_h)

          value
        end
      end
    end
  end
end
