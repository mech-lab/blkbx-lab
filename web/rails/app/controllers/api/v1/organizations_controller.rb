module Api
  module V1
    class OrganizationsController < BaseController
      before_action :require_user!

      def index
        render_collection(policy_scope(Organization))
      end

      def show
        organization = policy_scope(Organization).find(params[:id])
        authorize organization
        render_record(organization)
      end

      def create
        organization = Organization.new(organization_params)
        authorize organization
        organization.save!
        Membership.find_or_create_by!(user: current_user, organization: organization) { |membership| membership.role = "owner" }
        session[:organization_id] = organization.id
        render_record(organization, status: :created)
      end

      def update
        organization = policy_scope(Organization).find(params[:id])
        authorize organization
        organization.update!(organization_params)
        render_record(organization)
      end

      private

      def organization_params
        params.require(:organization).permit(:name, :slug, metadata: {})
      end

      def require_user!
        authenticate_user!
        Current.user = current_user
      end
    end
  end
end
