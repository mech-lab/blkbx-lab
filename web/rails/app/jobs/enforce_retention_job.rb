class EnforceRetentionJob < ApplicationJob
  queue_as :default

  def perform
    SharedBundle.where("expires_at < ?", Time.current).find_each do |bundle|
      next unless bundle.active?

      bundle.update!(status: "expired")
      AuditEvent.record!("bundle.expired", auditable: bundle, organization: bundle.organization, workspace: bundle.workspace, request_id: "retention-#{Time.current.to_i}", resulting_state: bundle.attributes)
    end
  end
end
