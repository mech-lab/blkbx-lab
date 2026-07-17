module Api
  module V1
    class ApiCredentialsController < BaseController
      def index
        return unless require_capability!("keys:manage")

        render_collection(Current.workspace.api_credentials.order(created_at: :desc))
      end

      def show
        return unless require_capability!("keys:manage")

        credential = Current.workspace.api_credentials.find(params[:id])
        render_record(credential)
      end

      def create
        return unless require_capability!("keys:manage")

        credential = Current.workspace.api_credentials.new(api_credential_params.merge(organization: Current.organization))
        credential.capabilities = Array(api_credential_params[:capabilities]).presence || ProductCatalog::SHARED_CAPABILITIES
        plaintext_secret = credential.issue_secret!(prefix: "cred")
        credential.save!
        render_record(credential, status: :created, extra: { plaintext_secret: plaintext_secret })
      end

      def destroy
        return unless require_capability!("keys:manage")

        credential = Current.workspace.api_credentials.find(params[:id])
        credential.update!(active: false)
        render json: { id: credential.id, active: credential.active }
      end

      private

      def api_credential_params
        params.require(:api_credential).permit(:name, :environment_id, :expires_at, capabilities: [])
      end
    end
  end
end
