module Accounts
  class SessionHandoffsController < AuthenticatedController
    skip_before_action :authenticate_user!, only: :consume
    before_action :ensure_identity_host!, only: :create

    def create
      result = Identity::IssueSessionHandoff.call(
        user: current_user,
        target_host: params.require(:target_host),
        organization: Current.organization,
        workspace: Current.workspace
      )

      render json: result, status: :created
    end

    def consume
      handoff = Identity::ConsumeSessionHandoff.call(token: params.require(:token), host: request.host)
      return render plain: "Invalid session handoff", status: :unauthorized unless handoff

      sign_in(handoff.user)
      session[:organization_id] = handoff.organization_id
      session[:workspace_id] = handoff.workspace_id
      redirect_to dashboard_path
    end

    private

    def ensure_identity_host!
      return if ProductCatalog.identity_host?(request.host)

      render plain: "Not found", status: :not_found
    end
  end
end
