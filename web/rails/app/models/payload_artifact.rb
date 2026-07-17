class PayloadArtifact < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  belongs_to :receipt

  validates :organization, :workspace, :receipt, :storage_key, :sha256, :byte_size, :content_type, presence: true
  validates :storage_key, uniqueness: true

  before_validation do
    self.storage_key ||= "payloads/#{organization_id}/#{SecureRandom.uuid}/payload.bin"
  end
end
