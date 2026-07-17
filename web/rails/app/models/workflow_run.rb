class WorkflowRun < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  belongs_to :workflow_definition
  belongs_to :customer_project, optional: true
  belongs_to :evidence_bundle, optional: true
  has_many :review_requests, dependent: :nullify
  has_many :control_executions, dependent: :destroy
  has_many :claims, dependent: :destroy
  has_many :decisions, dependent: :destroy
  has_many :approvals, dependent: :destroy
  has_many :workflow_exceptions, dependent: :destroy
  has_many :remediations, dependent: :destroy

  enum status: {
    draft: "draft",
    collecting: "collecting",
    verifying: "verifying",
    review_pending: "review_pending",
    approved: "approved",
    rejected: "rejected",
    exported: "exported",
    archived: "archived"
  }

  validates :organization, :workspace, :workflow_definition, :title, :status, presence: true
end
