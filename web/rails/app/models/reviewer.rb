class Reviewer < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  belongs_to :customer_organization, optional: true
  belongs_to :user, optional: true
  has_many :review_requests, dependent: :nullify
  has_many :portal_accesses, dependent: :nullify
  has_many :download_events, dependent: :nullify
  has_many :approvals, dependent: :nullify

  validates :organization, :workspace, :email, :name, :role, presence: true
end
