module Blkbxs
  module Sprint
    class BuildExceptionRegister
      def self.call(loan_case)
        new(loan_case).call
      end

      def initialize(loan_case)
        @loan_case = loan_case
      end

      def call
        rows = []
        graph_failures.each do |failure|
          rows << {
            "severity" => "high",
            "status" => "open",
            "title" => failure["code"],
            "description" => failure["message"],
            "resolution" => nil
          }
        end
        missing_evidence.each do |evidence_id|
          rows << {
            "severity" => "medium",
            "status" => "open",
            "title" => "missing_evidence",
            "description" => "Referenced evidence #{evidence_id} is not present in the evidence manifest.",
            "resolution" => nil
          }
        end
        rows
      end

      private

      def validation
        @validation ||= begin
          receipts = @loan_case.receipts.to_a
          receipts.empty? ? { "failures" => [], "evidence_summary" => {} } : UbrGraph.validate(receipts, evidence_manifest: fixture["evidence_manifest"], verifier_report: fixture["verifier_report"])
        end
      end

      def graph_failures
        Array(validation["failures"])
      end

      def missing_evidence
        Array(validation.dig("evidence_summary", "missing"))
      end

      def fixture
        @fixture ||= DemoCatalog.fetch(DemoCatalog::CANONICAL_EXTERNAL_SCENARIO)
      end
    end
  end
end
