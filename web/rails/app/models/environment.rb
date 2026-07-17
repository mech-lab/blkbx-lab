class Environment < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  belongs_to :application
  has_many :api_credentials, dependent: :destroy
  has_many :webhook_endpoints, dependent: :destroy

  enum environment_type: {
    development: "development",
    staging: "staging",
    production: "production"
  }

  validates :name, presence: true
  validates :environment_type, presence: true
  validates :name, uniqueness: { scope: :application_id }

  def production?
    environment_type == "production"
  end
end
