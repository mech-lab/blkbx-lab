module Blkbxs
  class ReviewerObjection < ApplicationRecord
    self.table_name = "blkbxs_reviewer_objections"

    BANK_FUNCTIONS = %w[credit compliance model_risk tprm legal audit infosec].freeze

    belongs_to :loan_case, class_name: "Blkbxs::LoanCase"

    validates :loan_case, :function, :severity, :status, :objection, presence: true
    validates :function, inclusion: { in: BANK_FUNCTIONS }
    validates :severity, inclusion: { in: %w[low medium high critical] }
    validates :status, inclusion: { in: %w[open responded resolved] }

    scope :open, -> { where(status: "open") }
  end
end
