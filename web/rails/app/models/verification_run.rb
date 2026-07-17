class VerificationRun < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  belongs_to :receipt
  belongs_to :verification_policy
  belongs_to :evidence_bundle, optional: true

  validates :organization, :workspace, :receipt, :verification_policy, :status, presence: true
  validates :status, inclusion: { in: %w[pending passed failed error] }

  scope :for_organization, ->(org) { where(organization: org) }
  scope :for_workspace, ->(ws) { where(workspace: ws) }
  scope :passed, -> { where(status: "passed") }
  scope :failed, -> { where(status: "failed") }
  scope :recent, -> { order(verified_at: :desc) }

  def passed?
    status == "passed"
  end

  def failed?
    status == "failed"
  end

  def error?
    status == "error"
  end
end
