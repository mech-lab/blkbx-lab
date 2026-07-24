module Api
  module V1
    module Blkbxs
      class UbrReceiptsController < WorkflowReceiptsController
        PRODUCT_TYPE = "blkbxs"
        WORKFLOW_KINDS = %w[ubr_event].freeze
        self.workflow_service = ::Blkbxs::CreateUbrReceipt

        def create
          return unless ensure_product_match!
          return unless require_capability!("receipts:write")

          _workflow_run, receipt = workflow_service.call(
            organization: Current.organization,
            workspace: Current.workspace,
            actor: current_user,
            body: workflow_params[:body_json] || {},
            domain_metadata: workflow_params[:domain_metadata] || {}
          )
          render_record(receipt, status: :created, extra: portable_receipt_extra(receipt))
        rescue Workflows::CreateReceipt::PortableReceiptRequiredError, ArgumentError => error
          render json: { error: error.message }, status: :unprocessable_entity
        end

        private

        def portable_receipt_extra(receipt)
          {
            portable_receipt: {
              available: receipt.portable_receipt.present?,
              key_id: receipt.signing_key_identifier,
              trust_registry_version: receipt.trust_registry_version,
              revocation_version: receipt.revocation_version,
              signer_request_id: receipt.signer_request_id
            }
          }
        end
      end
    end
  end
end
