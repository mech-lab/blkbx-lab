class DownloadEventsController < ApplicationController
  def create
    bundle = SharedBundle.find(params[:shared_bundle_id])
    access = PortalAccessAuthenticator.call(token: params.require(:token), shared_bundle: bundle)
    return render plain: "Unauthorized", status: :unauthorized unless access

    event = DownloadEvent.create!(
      organization: bundle.organization,
      workspace: bundle.workspace,
      shared_bundle: bundle,
      portal_access: access,
      reviewer: access.reviewer,
      artifact_type: params.fetch(:artifact_type, "bundle_zip"),
      metadata: params[:metadata] || {},
      downloaded_at: Time.current
    )
    AuditEvent.record!("bundle.downloaded", auditable: event, organization: bundle.organization, workspace: bundle.workspace, request_id: request.request_id, resulting_state: event.attributes)
    render json: event.as_json, status: :created
  end
end
