class VerificationPolicy < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  belongs_to :trust_registry, optional: true
  belongs_to :schema_definition, optional: true
  has_many :verification_runs, dependent: :destroy

  validates :organization, :workspace, :name, :policy_json, presence: true

  scope :for_organization, ->(org) { where(organization: org) }
  scope :for_workspace, ->(ws) { where(workspace: ws) }
  scope :active, -> { where(active: true) }

  def product_type
    workspace&.product_type
  end
end
