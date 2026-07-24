module Blkbxs
  class LoanCase < ApplicationRecord
    self.table_name = "blkbxs_loan_cases"

    SCENARIO_TYPE = "smb_250k_conditional_approval".freeze
    STATE_SEQUENCE = %w[
      draft
      intake_complete
      documents_received
      ai_extraction_complete
      credit_analysis_complete
      human_review_complete
      conditional_approval_issued
      evidence_bundle_generated
      verification_passed
      verification_warned
      verification_failed
      bank_review_complete
      final_packet_delivered
    ].freeze

    belongs_to :organization
    belongs_to :workspace
    belongs_to :sprint_engagement, class_name: "Blkbxs::SprintEngagement"

    has_many :evidence_events, -> { order(:event_order, :occurred_at, :id) }, class_name: "Blkbxs::EvidenceEvent", dependent: :destroy
    has_many :receipts, through: :evidence_events
    has_many :reviewer_objections, class_name: "Blkbxs::ReviewerObjection", dependent: :destroy
    has_many :export_packages, class_name: "Blkbxs::ExportPackage", dependent: :destroy

    validates :organization, :workspace, :sprint_engagement, :case_number, :status, :scenario_type, presence: true
    validates :case_number, uniqueness: { scope: :workspace_id }
    validates :scenario_type, inclusion: { in: [SCENARIO_TYPE] }
    validates :status, inclusion: { in: STATE_SEQUENCE }
    validate :workspace_belongs_to_organization
    validate :engagement_belongs_to_workspace

    scope :for_workspace, ->(workspace) { where(workspace: workspace) }
    scope :recent, -> { order(created_at: :desc) }

    def latest_evidence_bundle
      workspace.evidence_bundles
        .where(bundle_type: "blkbxs_ubr_graph")
        .select { |bundle| bundle.manifest["loan_case_id"] == id || bundle.manifest["case_number"] == case_number }
        .max_by(&:created_at)
    end

    def latest_verification_run
      VerificationRun.where(receipt: receipts).recent.first
    end

    def packet_readiness_score
      signed = receipts.count { |receipt| receipt.portable_receipt.present? }
      expected = 8
      score = ((signed.to_f / expected) * 100).round
      score.clamp(0, 100)
    end

    private

    def workspace_belongs_to_organization
      return if workspace.blank? || organization.blank? || workspace.organization_id == organization_id

      errors.add(:workspace, "must belong to the loan case organization")
    end

    def engagement_belongs_to_workspace
      return if sprint_engagement.blank? || workspace.blank? || sprint_engagement.workspace_id == workspace_id

      errors.add(:sprint_engagement, "must belong to the loan case workspace")
    end
  end
end
