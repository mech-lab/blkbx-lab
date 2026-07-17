class WorkflowDefinition < ApplicationRecord
  belongs_to :organization, optional: true
  belongs_to :workspace, optional: true
  has_many :workflow_runs, dependent: :nullify
  has_many :controls, dependent: :nullify

  validates :product_type, :workflow_kind, :name, presence: true
end
