class Claim < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  belongs_to :receipt, optional: true
  belongs_to :workflow_run, optional: true

  validates :organization, :workspace, :kind, presence: true
end
