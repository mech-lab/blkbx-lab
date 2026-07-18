module Api
  module V1
    class TrustPublicationsController < BaseController
      def index
        return unless require_capability!("keys:manage")

        render_collection(workspace.trust_publications.current_first)
      end

      def show
        return unless require_capability!("keys:manage")

        render_record(workspace.trust_publications.find(params[:id]))
      end

      def current
        return unless require_capability!("keys:manage")

        scope = workspace.trust_publications.current_first
        scope = scope.where(artifact_kind: params[:artifact_kind]) if params[:artifact_kind].present?
        render_record(scope.first || TrustPublication.new(artifact_kind: params[:artifact_kind], state: "missing"))
      end

      private

      def workspace
        Current.workspace || Workspace.find(params[:workspace_id])
      end
    end
  end
end
