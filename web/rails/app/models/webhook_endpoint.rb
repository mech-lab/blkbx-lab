class WebhookEndpoint < ApplicationRecord
  include TokenSecret

  belongs_to :organization
  belongs_to :workspace
  belongs_to :environment, optional: true

  validates :organization, :workspace, :url, :token_identifier, :secret_hash, presence: true
  validates :token_identifier, uniqueness: true

  scope :for_workspace, ->(ws) { where(workspace: ws) }
  scope :active, -> { where(active: true) }

  def usable?
    active? && secret_hash.present?
  end
end
