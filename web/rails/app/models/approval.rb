class Approval < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  belongs_to :review_request, optional: true
  belongs_to :workflow_run, optional: true
  belongs_to :user, optional: true
  belongs_to :reviewer, optional: true

  enum status: {
    approved: "approved",
    rejected: "rejected",
    pending: "pending"
  }

  validates :organization, :workspace, :status, presence: true
end
