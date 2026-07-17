class ReviewRequestsController < ApplicationController
  def update
    request_record = ReviewRequest.find(params[:id])
    bundle = request_record.shared_bundles.first || request_record.evidence_bundle.shared_bundles.first
    access = PortalAccessAuthenticator.call(token: params.require(:token), shared_bundle: bundle)
    return render plain: "Unauthorized", status: :unauthorized unless access

    approval = Approval.create!(
      organization: request_record.organization,
      workspace: request_record.workspace,
      review_request: request_record,
      reviewer: access.reviewer,
      status: params.require(:status),
      notes: params[:notes],
      decided_at: Time.current,
      metadata: params[:metadata] || {}
    )
    request_record.update!(status: approval.status == "approved" ? "approved" : "rejected", decision_notes: approval.notes)
    AuditEvent.record!("review.#{request_record.status}", auditable: approval, organization: request_record.organization, workspace: request_record.workspace, request_id: request.request_id, resulting_state: approval.attributes)
    render json: request_record.as_json.merge(approval: approval.as_json)
  end
end
