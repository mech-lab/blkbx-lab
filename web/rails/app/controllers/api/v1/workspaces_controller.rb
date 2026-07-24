module Api
  module V1
    class WorkspacesController < BaseController
      before_action :require_user!
      before_action :set_organization, only: %i[index show create update select seed_demo]
      before_action :set_workspace, only: %i[show update select seed_demo]

      def index
        authorize @organization, :show?
        render_collection(@organization.workspaces)
      end

      def show
        authorize @workspace
        render_record(@workspace)
      end

      def create
        authorize @organization, :update?
        workspace = @organization.workspaces.create!(workspace_params)
        session[:organization_id] = @organization.id
        session[:workspace_id] = workspace.id
        Current.organization = @organization
        Current.workspace = workspace
        seed_workspace_if_requested!(workspace)
        render_record(workspace, status: :created, extra: workspace_extra(workspace))
      end

      def update
        authorize @workspace
        @workspace.update!(workspace_params)
        render_record(@workspace, extra: workspace_extra(@workspace))
      end

      def select
        authorize @workspace, :show?
        session[:organization_id] = @organization.id
        session[:workspace_id] = @workspace.id
        Current.organization = @organization
        Current.workspace = @workspace
        render_record(@workspace, extra: workspace_extra(@workspace).merge(selected: true))
      end

      def seed_demo
        authorize @workspace, :update?
        result = seed_workspace_demo!(@workspace)
        render_record(@workspace.reload, extra: workspace_extra(@workspace).merge(seed_result: result))
      rescue ArgumentError => error
        render json: { error: error.message }, status: :unprocessable_entity
      end

      private

      def set_organization
        @organization = policy_scope(Organization).find(params[:organization_id])
      end

      def set_workspace
        @workspace = policy_scope(Workspace).find_by!(organization_id: params[:organization_id], id: params[:id])
      end

      def workspace_params
        params.require(:workspace).permit(:name, :slug, :product_type, :active, metadata: {})
      end

      def workspace_extra(workspace)
        extra = {
          selection: {
            organization_id: workspace.organization_id,
            workspace_id: workspace.id
          }
        }
        if workspace.product_type == "mand8"
          extra[:mand8] = ::Mand8::WorkspaceSnapshot.call(workspace)
        elsif workspace.product_type == "blkbxs"
          extra[:blkbxs] = ::Blkbxs::WorkspaceSnapshot.call(workspace)
        end
        extra
      end

      def seed_workspace_if_requested!(workspace)
        scenario = workspace.metadata["demo_scenario"].presence || workspace.metadata["seed_demo_scenario"].presence
        return if scenario.blank?

        seed_workspace_demo!(workspace, scenario: scenario)
      end

      def seed_workspace_demo!(workspace, scenario: nil)
        case workspace.product_type
        when "mand8"
          resolved = scenario.presence || params[:scenario].presence || workspace.metadata["demo_scenario"] || ::Mand8::DemoCatalog::CANONICAL_EXTERNAL_SCENARIO
          ::Mand8::SeedDemoWorkspace.call(workspace: workspace, scenario: resolved, actor: current_user)
        when "blkbxs"
          resolved = scenario.presence || params[:scenario].presence || workspace.metadata["demo_scenario"] || ::Blkbxs::DemoCatalog::CANONICAL_EXTERNAL_SCENARIO
          raise ArgumentError, "Unknown BLKBXS demo scenario: #{resolved}" unless resolved == ::Blkbxs::DemoCatalog::CANONICAL_EXTERNAL_SCENARIO

          ::Blkbxs::Sprint::SeedSmb250kCase.call(
            organization: workspace.organization,
            workspace: workspace,
            actor: current_user,
            issue_events: ActiveModel::Type::Boolean.new.cast(params[:seed_events])
          )
        else
          raise ArgumentError, "workspace product mismatch"
        end
      end

      def require_user!
        authenticate_user!
        Current.user = current_user
      end
    end
  end
end
