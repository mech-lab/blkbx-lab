class Control < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  belongs_to :workflow_definition, optional: true
  has_many :control_executions, dependent: :destroy

  validates :organization, :workspace, :name, :kind, presence: true
end
