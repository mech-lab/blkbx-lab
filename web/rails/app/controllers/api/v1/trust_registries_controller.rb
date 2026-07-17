module Api
  module V1
    class TrustRegistriesController < BaseController
      def index
        return unless require_capability!("trust_registries:read")

        render_collection(Current.workspace.trust_registries.order(created_at: :desc))
      end

      def show
        return unless require_capability!("trust_registries:read")

        registry = Current.workspace.trust_registries.find(params[:id])
        render_record(registry)
      end

      def create
        return unless require_capability!("keys:manage")

        registry = Current.workspace.trust_registries.create!(trust_registry_params.merge(organization: Current.organization))
        render_record(registry, status: :created)
      end

      private

      def trust_registry_params
        params.require(:trust_registry).permit(:name, :active, registry_json: {}, trust_anchors: [])
      end
    end
  end
end
