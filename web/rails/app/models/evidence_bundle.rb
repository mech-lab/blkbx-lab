class EvidenceBundle < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  belongs_to :workflow_run, optional: true
  belongs_to :created_by, class_name: "User", optional: true
  has_many :evidence_bundle_artifacts, dependent: :destroy
  has_many :evidence_artifacts, through: :evidence_bundle_artifacts
  has_many :verification_runs, dependent: :destroy
  has_many :shared_bundles, dependent: :destroy
  has_many :download_events, dependent: :destroy
  has_many :receipts, -> { distinct }, through: :evidence_artifacts

  validates :organization, :workspace, :bundle_type, presence: true

  scope :for_organization, ->(org) { where(organization: org) }
  scope :for_workspace, ->(ws) { where(workspace: ws) }
  scope :by_type, ->(type) { where(bundle_type: type) }

  def product_type
    workspace&.product_type
  end

  def manifest_path
    storage_key.presence || "bundles/#{organization_id}/#{id}/bundle.zip"
  end
end
