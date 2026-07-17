class IssuePortalAccessJob < ApplicationJob
  queue_as :default

  def perform(shared_bundle_id, reviewer_id, actor_id = nil)
    shared_bundle = SharedBundle.find(shared_bundle_id)
    reviewer = Reviewer.find(reviewer_id)
    actor = actor_id.present? ? User.find_by(id: actor_id) : nil

    access = PortalAccess.new(
      organization: shared_bundle.organization,
      workspace: shared_bundle.workspace,
      shared_bundle: shared_bundle,
      reviewer: reviewer,
      expires_at: shared_bundle.expires_at || 14.days.from_now
    )
    access.issue_secret!(prefix: "portal")
    access.save!

    AuditEvent.record!("portal.access_issued", auditable: access, organization: shared_bundle.organization, workspace: shared_bundle.workspace, user: actor, request_id: Current.request_id, resulting_state: access.attributes)
    access
  end
end
