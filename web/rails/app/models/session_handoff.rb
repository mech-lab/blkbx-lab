class SessionHandoff < ApplicationRecord
  include TokenSecret

  belongs_to :user
  belongs_to :organization, optional: true
  belongs_to :workspace, optional: true

  validates :user, :target_host, :token_identifier, :secret_hash, :expires_at, presence: true
  validates :token_identifier, uniqueness: true

  scope :active, -> { where(used_at: nil).where("expires_at > ?", Time.current) }

  def expired?
    expires_at <= Time.current
  end
end
