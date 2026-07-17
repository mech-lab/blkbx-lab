class AuditEvent < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace, optional: true
  belongs_to :user, optional: true
  belongs_to :api_credential, optional: true

  validates :organization, :event_type, :occurred_at, presence: true

  scope :recent, -> { order(occurred_at: :desc) }
  scope :for_workspace, ->(workspace) { where(workspace: workspace) }

  def self.record!(event_type, auditable:, organization:, workspace: nil, user: nil, api_credential: nil, request_id: nil, prior_state: nil, resulting_state: nil, metadata: {})
    create!(
      organization: organization,
      workspace: workspace,
      user: user,
      api_credential: api_credential,
      event_type: event_type,
      auditable_type: auditable.class.name,
      auditable_id: auditable.id,
      request_id: request_id,
      prior_state: prior_state,
      resulting_state: resulting_state,
      metadata: metadata,
      occurred_at: Time.current
    )
  end
end
