class ApplicationController < ActionController::Base
  include Pundit::Authorization

  protect_from_forgery with: :exception
  before_action :assign_current_request_context

  helper_method :current_product, :current_organization, :current_workspace, :current_user

  rescue_from Pundit::NotAuthorizedError, with: :render_forbidden

  private

  def assign_current_request_context
    Current.request_id = request.request_id
    Current.user = current_user if respond_to?(:current_user, true)
    Current.product ||= ProductCatalog.product_for_host(request.host)
    Current.brand ||= ProductCatalog.brand_for(Current.product)
    Current.organization ||= resolve_current_organization
    Current.workspace ||= resolve_current_workspace
    persist_selected_context if Current.user.present?
  end

  def resolve_current_organization
    return Current.api_credential.organization if Current.api_credential
    return unless Current.user

    requested_id = params[:organization_id] || session[:organization_id]
    scope = Current.user.organizations.order(:id)
    requested_id.present? ? scope.find_by(id: requested_id) || scope.first : scope.first
  end

  def resolve_current_workspace
    return Current.api_credential.workspace if Current.api_credential
    return unless Current.organization

    requested_id = params[:workspace_id] || session[:workspace_id]
    scope = Current.organization.workspaces.order(:id)
    if requested_id.present?
      scope.find_by(id: requested_id) || scope.find_by(product_type: Current.product) || scope.first
    else
      scope.find_by(product_type: Current.product) || scope.first
    end
  end

  def persist_selected_context
    session[:organization_id] = Current.organization&.id
    session[:workspace_id] = Current.workspace&.id
  end

  def current_product
    Current.product
  end

  def current_user
    Current.user || super
  end

  def current_organization
    Current.organization
  end

  def current_workspace
    Current.workspace
  end

  def render_forbidden
    respond_to do |format|
      format.html { render plain: "Forbidden", status: :forbidden }
      format.json { render json: { error: "forbidden" }, status: :forbidden }
    end
  end
end
