class SchemaDefinition < ApplicationRecord
  belongs_to :organization, optional: true
  has_many :receipts, dependent: :nullify
  has_many :verification_policies, dependent: :nullify

  validates :schema_key, :schema_version, :schema_json, :domain, presence: true
  validates :schema_version, uniqueness: { scope: %i[schema_key organization_id] }
  validates :domain, presence: true, inclusion: { in: %w[ink blkbxs mand8 due] }

  scope :for_domain, ->(domain) { where(domain: domain) }
  scope :active, -> { where(active: true) }
  scope :by_key, ->(key) { where(schema_key: key) }
  scope :by_version, ->(version) { where(schema_version: version) }

  def self.latest_for(domain, key)
    for_domain(domain).by_key(key).active.order(schema_version: :desc).first
  end
end
