module Blkbxs
  module Sprint
    class BuildClaimsBoundaryMatrix
      def self.call(loan_case)
        new(loan_case).call
      end

      def initialize(loan_case)
        @loan_case = loan_case
      end

      def call
        [
          row("Application intake occurred", "supported", receipt_ref("consent.granted"), nil),
          row("Documents were fingerprinted", "supported", receipt_ref("documents.received"), nil),
          row("AI extraction or analysis output was preserved", "supported", receipt_ref("cashflow.analysis_completed"), nil),
          row("Human reviewed the recommendation", "supported", receipt_ref("human_credit_review.completed"), nil),
          row("Conditional approval was evidence-linked", "supported", decision_ref, nil),
          row("The borrower will repay", "unsupported", nil, "Outside BLKBXS claim boundary."),
          row("The bank is regulatorily compliant", "unsupported", nil, "Outside BLKBXS claim boundary.")
        ]
      end

      private

      def row(claim_text, claim_status, evidence_reference, limitation)
        {
          "claim_text" => claim_text,
          "claim_status" => claim_status,
          "evidence_reference" => evidence_reference,
          "limitation" => limitation
        }
      end

      def decision_ref
        [receipt_ref("loan.application_decisioned"), receipt_ref("conditional_approval_notice.generated")].compact.join(" + ").presence
      end

      def receipt_ref(operation_name)
        event = @loan_case.evidence_events.find { |record| record.event_type == operation_name }
        return unless event&.receipt

        "#{operation_name}: receipt #{event.receipt.id}"
      end
    end
  end
end
