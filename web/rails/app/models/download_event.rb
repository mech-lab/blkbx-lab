class DownloadEvent < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  belongs_to :shared_bundle
  belongs_to :portal_access, optional: true
  belongs_to :reviewer, optional: true

  validates :organization, :workspace, :shared_bundle, :artifact_type, :downloaded_at, presence: true
end
