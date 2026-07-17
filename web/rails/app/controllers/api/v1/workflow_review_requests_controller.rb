module Api
  module V1
    class WorkflowReviewRequestsController < BaseController
      def index
        render_collection(Current.workspace.review_requests.order(created_at: :desc))
      end

      def show
        request = Current.workspace.review_requests.find(params[:id])
        render_record(request)
      end

      def create
        return unless ensure_product_match!
        return unless require_capability!("bundles:create")

        bundle = Current.workspace.evidence_bundles.find(params.require(:evidence_bundle_id))
        review_request, shared_bundle = Workflows::CreateReviewRequest.call(
          organization: Current.organization,
          workspace: Current.workspace,
          evidence_bundle: bundle,
          title: params.fetch(:title, "#{Current.brand} review"),
          reviewer_email: params.require(:reviewer).fetch(:email),
          reviewer_name: params.require(:reviewer).fetch(:name),
          reviewer_role: params.require(:reviewer).fetch(:role),
          actor: current_user
        )

        render json: review_request.as_json.merge(shared_bundle: shared_bundle.as_json), status: :created
      end

      def update
        return unless require_capability!("bundles:create")

        request = Current.workspace.review_requests.find(params[:id])
        request.update!(status: params.require(:status))
        render_record(request)
      end

      private

      def ensure_product_match!
        return true if Current.workspace.product_type == self.class::PRODUCT_TYPE

        render json: { error: "workspace product mismatch" }, status: :unprocessable_entity
        false
      end
    end
  end
end
