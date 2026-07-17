class SharedBundle < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  belongs_to :evidence_bundle
  belongs_to :review_request, optional: true
  has_many :portal_accesses, dependent: :destroy
  has_many :download_events, dependent: :destroy

  enum status: {
    active: "active",
    revoked: "revoked",
    expired: "expired"
  }

  validates :organization, :workspace, :evidence_bundle, :name, :status, presence: true
end
