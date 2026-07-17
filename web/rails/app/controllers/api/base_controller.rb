module Api
  class BaseController < ApplicationController
    protect_from_forgery with: :null_session
    before_action :authenticate_api_actor!

    private

    def authenticate_api_actor!
      token = bearer_token
      if token.present?
        credential = ApiCredentialAuthenticator.call(token: token)
        return render json: { error: "unauthorized" }, status: :unauthorized unless credential

        Current.api_credential = credential
        Current.organization = credential.organization
        Current.workspace = credential.workspace
        return
      end

      authenticate_user!
      Current.user = current_user
    end

    def require_capability!(capability)
      return true unless Current.api_credential
      return true if Current.api_credential.has_capability?(capability)

      render json: { error: "missing capability", capability: capability }, status: :forbidden
      false
    end

    def bearer_token
      header = request.authorization.to_s
      return if header.blank?

      scheme, value = header.split(" ", 2)
      return unless scheme&.casecmp("Bearer")&.zero?

      value
    end
  end
end
