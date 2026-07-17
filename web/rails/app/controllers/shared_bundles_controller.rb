class SharedBundlesController < ApplicationController
  def show
    bundle = SharedBundle.find(params[:id])
    access = PortalAccessAuthenticator.call(token: params.require(:token), shared_bundle: bundle)
    return render plain: "Unauthorized", status: :unauthorized unless access

    payload = {
      shared_bundle: bundle.as_json,
      evidence_bundle: bundle.evidence_bundle.as_json,
      review_request: bundle.review_request&.as_json
    }
    if bundle.workspace.product_type == "mand8"
      payload[:mand8] = {
        case_summary: Mand8::WorkspaceSnapshot.case_summary_for_bundle(bundle.evidence_bundle),
        verifier_handoff: bundle.evidence_bundle.manifest["verifier_handoff"]
      }
    end
    render json: payload
  end
end
