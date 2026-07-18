module Api
  module V1
    class SigningKeysController < BaseController
      def index
        return unless require_capability!("keys:manage")

        render_collection(workspace.signing_keys.order(created_at: :desc))
      end

      def show
        return unless require_capability!("keys:manage")

        render_record(workspace.signing_keys.find(params[:id]))
      end

      def create
        return unless require_capability!("keys:manage")

        key = workspace.signing_keys.create!(
          signing_key_params.merge(
            organization: organization,
            state: signing_key_params[:state].presence || "pre_active"
          )
        )
        render_record(key, status: :created)
      end

      private

      def workspace
        Current.workspace || Workspace.find(params[:workspace_id] || params.dig(:signing_key, :workspace_id))
      end

      def organization
        Current.organization || workspace.organization
      end

      def signing_key_params
        params.require(:signing_key).permit(
          :workspace_id,
          :issuer_id,
          :key_identifier,
          :public_key,
          :key_type,
          :state,
          :usage,
          :custody_kind,
          :external_reference,
          :expires_at,
          metadata: {}
        )
      end
    end
  end
end
