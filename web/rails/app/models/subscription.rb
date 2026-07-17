class Subscription < ApplicationRecord
  belongs_to :organization
  belongs_to :billing_account
  belongs_to :plan

  validates :organization, :billing_account, :plan, :status, presence: true

  enum status: {
    active: "active",
    trialing: "trialing",
    past_due: "past_due",
    cancelled: "cancelled"
  }

  scope :for_organization, ->(org) { where(organization: org) }
  scope :active, -> { where(status: "active") }
  scope :current, -> { where("current_period_end > ?", Time.current) }

  def product_type
    plan&.product_type
  end

  def expired?
    current_period_end.present? && current_period_end < Time.current
  end
end
