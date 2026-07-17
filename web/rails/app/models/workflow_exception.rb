class WorkflowException < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  belongs_to :workflow_run
  belongs_to :receipt, optional: true
  has_many :remediations, dependent: :destroy

  enum status: {
    open: "open",
    acknowledged: "acknowledged",
    resolved: "resolved"
  }

  validates :organization, :workspace, :workflow_run, :kind, :status, presence: true
end
