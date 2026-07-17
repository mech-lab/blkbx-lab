class CustomerOrganization < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  has_many :customer_projects, dependent: :destroy
  has_many :reviewers, dependent: :destroy

  validates :organization, :workspace, :name, :slug, presence: true
  validates :slug, uniqueness: { scope: :organization_id }
end
