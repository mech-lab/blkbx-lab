class Membership < ApplicationRecord
  belongs_to :user
  belongs_to :organization

  enum role: {
    owner: "owner",
    administrator: "administrator",
    developer: "developer",
    compliance: "compliance",
    reviewer: "reviewer",
    customer_reviewer: "customer_reviewer",
    read_only_auditor: "read_only_auditor"
  }

  validates :role, presence: true
  validates :user_id, uniqueness: { scope: :organization_id }

  scope :owners, -> { where(role: "owner") }
  scope :administrators, -> { where(role: ["owner", "administrator"]) }
  scope :developers, -> { where(role: "developer") }
  scope :reviewers, -> { where(role: ["reviewer", "customer_reviewer"]) }
end
