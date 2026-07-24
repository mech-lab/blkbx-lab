module Blkbxs
  module Sprint
    class GraphSummary
      def self.call(loan_case)
        new(loan_case).call
      end

      def initialize(loan_case)
        @loan_case = loan_case
      end

      def call
        receipts = @loan_case.receipts.to_a
        validation = validate(receipts)
        {
          "loan_case" => loan_case_payload,
          "sprint_engagement" => @loan_case.sprint_engagement.as_json(only: %i[id name status starts_on ends_on metadata]),
          "timeline" => timeline_payload,
          "receipt_count" => receipts.length,
          "signed_receipt_count" => receipts.count { |receipt| receipt.portable_receipt.present? },
          "packet_readiness_score" => @loan_case.packet_readiness_score,
          "business_process_id" => validation["business_process_id"],
          "graph_validation" => validation,
          "decision_summary" => receipts.any? ? UbrGraph.decision_summary(receipts) : {},
          "evidence_summary" => validation["evidence_summary"] || {},
          "ai_boundary_summary" => validation["ai_boundary_summary"] || {},
          "latest_verification_status" => @loan_case.latest_verification_run&.status,
          "latest_evidence_bundle_id" => @loan_case.latest_evidence_bundle&.id,
          "open_objection_count" => @loan_case.reviewer_objections.open.count,
          "verifier_handoff" => verifier_handoff(validation)
        }
      end

      private

      def loan_case_payload
        @loan_case.as_json(
          only: %i[
            id case_number status scenario_type borrower_name bank_reviewer_name
            requested_amount metadata created_at updated_at
          ]
        )
      end

      def timeline_payload
        @loan_case.evidence_events.ordered.map do |event|
          {
            "id" => event.id,
            "external_id" => event.external_id,
            "event_type" => event.event_type,
            "actor_type" => event.actor_type,
            "actor_identifier" => event.actor_identifier,
            "source_system" => event.source_system,
            "canonical_hash" => event.canonical_hash,
            "previous_event_hash" => event.previous_event_hash,
            "event_order" => event.event_order,
            "occurred_at" => event.occurred_at,
            "receipt_id" => event.receipt_id,
            "signed" => event.signed?,
            "portable_receipt_key_id" => event.receipt&.signing_key_identifier
          }
        end
      end

      def validate(receipts)
        return empty_validation if receipts.empty?

        UbrGraph.validate(receipts, evidence_manifest: fixture["evidence_manifest"], verifier_report: fixture["verifier_report"])
      end

      def empty_validation
        {
          "valid" => false,
          "business_process_id" => nil,
          "receipt_count" => 0,
          "topological_order" => [],
          "root_receipts" => [],
          "terminal_receipts" => [],
          "evidence_summary" => {},
          "ai_boundary_summary" => {},
          "failures" => [
            {
              "code" => "receipt_graph_empty",
              "message" => "No signed BLKBXS UBR receipts have been issued for this loan case."
            }
          ]
        }
      end

      def verifier_handoff(validation)
        return { "product" => "blkbxs", "available" => false, "reason_code" => "RECEIPT_GRAPH_EMPTY" } if @loan_case.receipts.empty?

        VerifierHandoff.payload(
          workspace: @loan_case.workspace,
          business_process_id: validation["business_process_id"],
          bundle_id: @loan_case.latest_evidence_bundle&.id
        )
      end

      def fixture
        @fixture ||= DemoCatalog.fetch(DemoCatalog::CANONICAL_EXTERNAL_SCENARIO)
      end
    end
  end
end
