module Blkbxs
  class EvidenceEvent < ApplicationRecord
    self.table_name = "blkbxs_evidence_events"

    belongs_to :loan_case, class_name: "Blkbxs::LoanCase"
    belongs_to :receipt, optional: true

    validates :loan_case, :external_id, :event_type, :actor_type, :payload, :occurred_at, presence: true
    validates :external_id, uniqueness: { scope: :loan_case_id }
    validates :receipt_id, uniqueness: true, allow_nil: true
    validate :receipt_matches_loan_case_workspace

    scope :ordered, -> { order(:event_order, :occurred_at, :id) }

    def signed?
      receipt&.portable_receipt.present?
    end

    private

    def receipt_matches_loan_case_workspace
      return if receipt.blank? || loan_case.blank?

      if receipt.workspace_id != loan_case.workspace_id || receipt.organization_id != loan_case.organization_id
        errors.add(:receipt, "must belong to the loan case workspace")
      end
    end
  end
end
