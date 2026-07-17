class UsageEvent < ApplicationRecord
  belongs_to :organization
  belongs_to :billing_account
  belongs_to :workspace, optional: true
  belongs_to :subscription, optional: true

  validates :organization, :billing_account, :event_type, :quantity, presence: true
  validates :quantity, numericality: { greater_than_or_equal_to: 0 }

  scope :for_organization, ->(org) { where(organization: org) }
  scope :for_workspace, ->(ws) { where(workspace: ws) }
  scope :by_type, ->(type) { where(event_type: type) }
  scope :recent, -> { order(occurred_at: :desc) }
  scope :in_period, ->(start_time, end_time) { where(occurred_at: start_time..end_time) }

  def self.track(event_type, organization:, workspace: nil, quantity: 1, metadata: {}, subscription: nil)
    create!(
      organization: organization,
      workspace: workspace,
      subscription: subscription,
      billing_account: organization.billing_account,
      event_type: event_type,
      quantity: quantity,
      metadata: metadata,
      occurred_at: Time.current
    )
  end
end
