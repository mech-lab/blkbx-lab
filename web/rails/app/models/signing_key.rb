class SigningKey < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  belongs_to :issuer, optional: true
  has_many :key_ceremonies, dependent: :nullify
  has_many :trust_publications, dependent: :nullify

  enum state: {
    pre_active: "pre_active",
    active: "active",
    retired: "retired",
    revoked: "revoked",
    expired: "expired"
  }

  validates :organization, :workspace, :key_identifier, :public_key, :key_type, :state, :usage, :custody_kind, presence: true
  validates :key_identifier, uniqueness: { scope: :organization_id }

  scope :for_organization, ->(org) { where(organization: org) }
  scope :active, -> { where(state: "active") }
  scope :receipt_signing, -> { where(usage: "receipt_signing") }
  scope :trust_publication, -> { where(usage: "trust_publication") }
end
