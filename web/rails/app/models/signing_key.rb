class SigningKey < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  belongs_to :issuer, optional: true

  enum state: {
    active: "active",
    revoked: "revoked",
    expired: "expired"
  }

  validates :organization, :workspace, :key_identifier, :public_key, :key_type, :state, presence: true
  validates :key_identifier, uniqueness: { scope: :organization_id }

  scope :for_organization, ->(org) { where(organization: org) }
  scope :active, -> { where(state: "active") }
end
