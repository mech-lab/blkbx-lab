class CustomerProject < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  belongs_to :customer_organization, optional: true
  has_many :review_requests, dependent: :nullify
  has_many :workflow_runs, dependent: :nullify

  validates :organization, :workspace, :name, :slug, :project_type, presence: true
  validates :slug, uniqueness: { scope: :organization_id }
end
