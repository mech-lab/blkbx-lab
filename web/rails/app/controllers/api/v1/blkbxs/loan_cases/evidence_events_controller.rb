module Api
  module V1
    module Blkbxs
      module LoanCases
        class EvidenceEventsController < BaseController
          before_action :ensure_blkbxs_workspace!

          def index
            return unless require_capability!("receipts:read")

            render json: loan_case.evidence_events.ordered.map { |event| event_payload(event) }
          end

          def create
            return unless require_capability!("receipts:write")

            event, receipt = ::Blkbxs::Sprint::BuildEvidenceEvent.call(
              loan_case: loan_case,
              body: body_param,
              actor: current_user,
              actor_type: params[:actor_type],
              actor_identifier: params[:actor_identifier],
              source_system: params[:source_system],
              domain_metadata: json_param(:domain_metadata) || {}
            )
            render json: event_payload(event).merge(receipt: receipt.as_json), status: :created
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
            @loan_case ||= Current.workspace.blkbxs_loan_cases.find(params[:loan_case_id])
          end

          def event_payload(event)
            event.as_json.merge(
              signed: event.signed?,
              receipt: event.receipt&.as_json
            )
          end

          def json_param(key)
            value = params[key]
            return nil if value.blank?
            return value.to_unsafe_h if value.respond_to?(:to_unsafe_h)
            return value.to_h if value.respond_to?(:to_h)

            value
          end

          def body_param
            value = params.require(:body_json)
            return value.to_unsafe_h if value.respond_to?(:to_unsafe_h)
            return value.to_h if value.respond_to?(:to_h)

            value
          end
        end
      end
    end
  end
end
