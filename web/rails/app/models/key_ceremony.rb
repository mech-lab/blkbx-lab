class KeyCeremony < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  belongs_to :signing_key, optional: true
  belongs_to :requested_by, class_name: "User", optional: true

  has_many :key_ceremony_approvals, dependent: :destroy
  has_many :trust_publications, dependent: :nullify

  enum state: {
    pending_approval: "pending_approval",
    approved: "approved",
    activated: "activated",
    retired: "retired",
    revoked: "revoked",
    published: "published"
  }

  validates :organization, :workspace, :ceremony_kind, :state, presence: true

  scope :recent, -> { order(created_at: :desc) }

  def approval_quorum_met?
    key_ceremony_approvals.approved.select(:approver_role).distinct.count >= 2
  end
end
