class Receipt < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  belongs_to :issuer, optional: true
  belongs_to :schema_definition, optional: true
  has_many :payload_artifacts, dependent: :destroy
  has_many :evidence_artifacts, dependent: :destroy
  has_many :verification_runs, dependent: :destroy
  has_many :control_executions, dependent: :nullify
  has_many :claims, dependent: :nullify
  has_many :decisions, dependent: :nullify
  has_many :workflow_exceptions, dependent: :nullify

  validates :organization, :workspace, :schema_key, :schema_version, presence: true
  validates :external_id, uniqueness: { scope: :organization_id }, allow_blank: true

  scope :for_organization, ->(org) { where(organization: org) }
  scope :for_workspace, ->(ws) { where(workspace: ws) }
  scope :by_schema, ->(key, version) { where(schema_key: key, schema_version: version) }

  def domain_specific?
    workflow_kind.present?
  end

  def product_type
    workspace&.product_type
  end
end
