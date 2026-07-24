module Blkbxs
  class SprintEngagement < ApplicationRecord
    self.table_name = "blkbxs_sprint_engagements"

    has_many :loan_cases, class_name: "Blkbxs::LoanCase", dependent: :destroy

    belongs_to :organization
    belongs_to :workspace

    validates :organization, :workspace, :name, :status, presence: true
    validates :name, uniqueness: { scope: :workspace_id }
    validates :status, inclusion: { in: %w[active completed paused cancelled] }
    validate :workspace_belongs_to_organization

    private

    def workspace_belongs_to_organization
      return if workspace.blank? || organization.blank? || workspace.organization_id == organization_id

      errors.add(:workspace, "must belong to the sprint organization")
    end
  end
end
