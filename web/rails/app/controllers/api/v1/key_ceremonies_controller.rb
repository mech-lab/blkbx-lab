module Api
  module V1
    class KeyCeremoniesController < BaseController
      def index
        return unless require_capability!("keys:manage")

        render_collection(workspace.key_ceremonies.recent)
      end

      def show
        return unless require_capability!("keys:manage")

        render_record(workspace.key_ceremonies.find(params[:id]))
      end

      def create
        return unless require_capability!("keys:manage")

        ceremony = workspace.key_ceremonies.create!(
          key_ceremony_params.merge(
            organization: organization,
            requested_by: Current.user
          )
        )
        render_record(ceremony, status: :created)
      end

      def approve
        return unless require_capability!("keys:manage")
        return render json: { error: "user approval required" }, status: :forbidden unless current_user

        ceremony = workspace.key_ceremonies.find(params[:id])
        approval = Keys::ApproveCeremony.call(ceremony: ceremony, actor: current_user, note: params[:note])
        render_record(ceremony, extra: { approval: approval.as_json })
      end

      def activate
        perform_transition!("activate")
      end

      def retire
        perform_transition!("retire")
      end

      def revoke
        perform_transition!("revoke")
      end

      def publish
        return unless require_capability!("keys:manage")

        ceremony = workspace.key_ceremonies.find(params[:id])
        publication = Keys::PublishTrustArtifact.call(
          ceremony: ceremony,
          artifact_kind: publish_params.fetch(:artifact_kind),
          version: publish_params.fetch(:version),
          artifact_json: publish_params[:artifact_json],
          artifact_url: publish_params[:artifact_url]
        )
        render_record(ceremony, extra: { trust_publication: publication.as_json })
      end

      private

      def perform_transition!(action)
        return unless require_capability!("keys:manage")

        ceremony = workspace.key_ceremonies.find(params[:id])
        Keys::ExecuteCeremony.call(ceremony: ceremony, action: action)
        render_record(ceremony)
      end

      def workspace
        Current.workspace || Workspace.find(params[:workspace_id] || params.dig(:key_ceremony, :workspace_id))
      end

      def organization
        Current.organization || workspace.organization
      end

      def key_ceremony_params
        params.require(:key_ceremony).permit(:workspace_id, :signing_key_id, :ceremony_kind, :scheduled_for, metadata: {})
      end

      def publish_params
        params.require(:trust_publication).permit(:artifact_kind, :version, :artifact_url, artifact_json: {})
      end
    end
  end
end
