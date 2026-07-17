class ControlExecution < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  belongs_to :control
  belongs_to :workflow_run, optional: true
  belongs_to :receipt, optional: true

  enum status: {
    pending: "pending",
    passed: "passed",
    failed: "failed",
    exception: "exception"
  }

  validates :organization, :workspace, :control, :status, presence: true
end
