class ReviewRequest < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  belongs_to :evidence_bundle
  belongs_to :workflow_run, optional: true
  belongs_to :customer_project, optional: true
  belongs_to :reviewer, optional: true
  has_many :approvals, dependent: :destroy
  has_many :shared_bundles, dependent: :destroy

  enum status: {
    pending: "pending",
    in_review: "in_review",
    approved: "approved",
    rejected: "rejected",
    expired: "expired"
  }

  validates :organization, :workspace, :evidence_bundle, :title, :status, presence: true
end
