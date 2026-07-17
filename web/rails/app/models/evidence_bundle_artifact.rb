class EvidenceBundleArtifact < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  belongs_to :evidence_bundle
  belongs_to :evidence_artifact

  validates :organization, :workspace, :evidence_bundle, :evidence_artifact, presence: true
  validates :evidence_artifact_id, uniqueness: { scope: :evidence_bundle_id }
end
