class Application < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  has_many :environments, dependent: :destroy
  has_many :sdk_installations, dependent: :destroy

  validates :name, :slug, presence: true
  validates :slug, uniqueness: { scope: :organization_id }

  def current_environment
    Current.environment
  end
end
