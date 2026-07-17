class BillingAccount < ApplicationRecord
  belongs_to :organization
  has_many :subscriptions, dependent: :destroy
  has_many :usage_events, dependent: :destroy
  has_many :invoice_references, dependent: :destroy

  validates :organization, :billing_provider, :status, presence: true

  enum status: {
    active: "active",
    suspended: "suspended",
    cancelled: "cancelled"
  }

  scope :for_organization, ->(org) { where(organization: org) }
  scope :active, -> { where(status: "active") }

  def current_subscription
    subscriptions.active.first
  end

  def current_plan
    current_subscription&.plan
  end
end
