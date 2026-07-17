class Issuer < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  has_many :signing_keys, dependent: :destroy
  has_many :receipts, dependent: :nullify

  validates :organization, :workspace, :name, :slug, :public_key, :key_type, presence: true
  validates :slug, uniqueness: { scope: :organization_id }

  scope :for_organization, ->(org) { where(organization: org) }
  scope :active, -> { where(active: true) }

  def current_workspace
    Current.workspace
  end
end
