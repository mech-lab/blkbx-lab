class ApiCredential < ApplicationRecord
  include TokenSecret

  belongs_to :organization
  belongs_to :workspace
  belongs_to :environment, optional: true

  validates :organization, :workspace, :name, :token_identifier, :secret_hash, presence: true
  validates :token_identifier, uniqueness: true

  CAPABILITIES = %w[
    receipts:write
    receipts:read
    verifications:create
    bundles:create
    trust_registries:read
    keys:manage
  ].freeze

  scope :for_workspace, ->(ws) { where(workspace: ws) }
  scope :for_organization, ->(org) { where(organization: org) }
  scope :active, -> { where(active: true) }

  def capabilities_list
    Array(capabilities)
  end

  def has_capability?(capability)
    capabilities_list.include?(capability)
  end

  def expired?
    expires_at.present? && expires_at < Time.current
  end

  def usable?
    active? && !expired?
  end
end
