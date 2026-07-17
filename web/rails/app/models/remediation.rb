class Remediation < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  belongs_to :workflow_exception
  belongs_to :workflow_run, optional: true

  enum status: {
    open: "open",
    in_progress: "in_progress",
    completed: "completed"
  }

  validates :organization, :workspace, :workflow_exception, :status, presence: true
end
