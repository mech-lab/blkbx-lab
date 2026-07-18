class KeyCeremonyApproval < ApplicationRecord
  belongs_to :key_ceremony
  belongs_to :user

  enum state: {
    approved: "approved"
  }

  validates :key_ceremony, :user, :approver_role, :state, :approved_at, presence: true
  validates :user_id, uniqueness: { scope: :key_ceremony_id }

  scope :approved, -> { where(state: "approved") }
end
