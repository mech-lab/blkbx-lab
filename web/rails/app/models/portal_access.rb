class PortalAccess < ApplicationRecord
  include TokenSecret

  belongs_to :organization
  belongs_to :workspace
  belongs_to :shared_bundle
  belongs_to :reviewer, optional: true
  has_many :download_events, dependent: :nullify

  validates :organization, :workspace, :shared_bundle, :token_identifier, :secret_hash, :expires_at, presence: true
  validates :token_identifier, uniqueness: true

  scope :active, -> { where(used_at: nil).where("expires_at > ?", Time.current) }

  def expired?
    expires_at <= Time.current
  end
end
