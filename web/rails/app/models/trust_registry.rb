class TrustRegistry < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  has_many :verification_policies, dependent: :nullify

  validates :organization, :workspace, :name, :registry_json, presence: true

  scope :for_organization, ->(org) { where(organization: org) }
  scope :active, -> { where(active: true) }

  def product_type
    Current.product
  end
end
