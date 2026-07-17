class EvidenceArtifact < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  belongs_to :receipt
  has_many :evidence_bundle_artifacts, dependent: :destroy
  has_many :evidence_bundles, through: :evidence_bundle_artifacts

  validates :organization, :workspace, :receipt, :storage_key, :sha256, :byte_size, :content_type, presence: true
  validates :storage_key, uniqueness: true

  before_validation do
    self.storage_key ||= "artifacts/#{organization_id}/#{SecureRandom.uuid}/artifact.bin"
  end
end
