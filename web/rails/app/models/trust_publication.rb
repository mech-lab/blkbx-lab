class TrustPublication < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  belongs_to :key_ceremony, optional: true
  belongs_to :signing_key, optional: true

  validates :organization, :workspace, :artifact_kind, :version, :state, presence: true
  validates :version, uniqueness: { scope: %i[organization_id artifact_kind] }

  scope :published, -> { where(state: "published") }
  scope :current_first, -> { order(published_at: :desc, created_at: :desc) }
end
