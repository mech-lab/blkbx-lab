require "digest"

module Blkbxs
  module Sprint
    class BuildEvidenceEvent
      SOURCE_SYSTEM = "bankabil_sprint_console".freeze

      def self.call(options = {})
        new(options).call
      end

      def initialize(options = {})
        @loan_case = options.fetch(:loan_case)
        @body = options.fetch(:body)
        @actor = options[:actor]
        @actor_type = options[:actor_type]
        @actor_identifier = options[:actor_identifier]
        @source_system = options[:source_system] || SOURCE_SYSTEM
        @event_order = options[:event_order]
        @previous_event_hash = options[:previous_event_hash]
        @domain_metadata = options[:domain_metadata] || {}
      end

      def call
        normalized_body = ReceiptContract.ubr_event(body: @body)
        existing = @loan_case.evidence_events.find_by(external_id: normalized_body.fetch("id"))
        return [existing, existing.receipt] if existing&.receipt&.portable_receipt.present?
        raise ArgumentError, "BLKBXS evidence event exists without a linked portable receipt" if existing

        ApplicationRecord.transaction do
          event = @loan_case.evidence_events.create!(
            external_id: normalized_body.fetch("id"),
            event_type: normalized_body.dig("operation", "name"),
            actor_type: @actor_type.presence || inferred_actor_type(normalized_body),
            actor_identifier: @actor_identifier.presence || inferred_actor_identifier(normalized_body),
            source_system: @source_system,
            payload: normalized_body,
            canonical_hash: canonical_hash(normalized_body),
            previous_event_hash: @previous_event_hash || previous_event_hash_for(normalized_body),
            event_order: @event_order || next_event_order,
            occurred_at: occurred_at(normalized_body)
          )

          _workflow_run, receipt = Blkbxs::CreateUbrReceipt.call(
            organization: @loan_case.organization,
            workspace: @loan_case.workspace,
            actor: @actor,
            body: normalized_body,
            domain_metadata: receipt_metadata(normalized_body)
          )
          event.update!(receipt: receipt)
          advance_loan_case!(normalized_body)
          [event, receipt]
        end
      end

      private

      def next_event_order
        @loan_case.evidence_events.maximum(:event_order).to_i + 1
      end

      def previous_event_hash_for(body)
        parent_ids = Array(body.dig("links", "parent_receipts"))
        parent_event = @loan_case.evidence_events.where(external_id: parent_ids).ordered.last if parent_ids.any?
        parent_event&.canonical_hash || @loan_case.evidence_events.ordered.last&.canonical_hash
      end

      def receipt_metadata(body)
        ReceiptContract.domain_metadata_for(body: body).merge(
          @domain_metadata.deep_stringify_keys
        ).merge(
          "loan_case_id" => @loan_case.id,
          "case_number" => @loan_case.case_number,
          "sprint_engagement_id" => @loan_case.sprint_engagement_id,
          "scenario_type" => @loan_case.scenario_type,
          "action_id" => body.fetch("id")
        )
      end

      def inferred_actor_type(body)
        operation_name = body.dig("operation", "name").to_s
        return "human_reviewer" if operation_name.include?("human")
        return "ai_assisted_system" if body.dig("ai_assistance", "used") == true

        "bank_system"
      end

      def inferred_actor_identifier(body)
        preferred_roles = case inferred_actor_type(body)
                          when "human_reviewer" then %w[human_approver reviewer issuer]
                          when "ai_assisted_system" then %w[ai_agent issuer]
                          else %w[issuer applicant_business]
                          end
        parties = Array(body["parties"])
        party = preferred_roles.lazy.filter_map { |role| parties.find { |item| item["role"] == role } }.first
        party&.[]("id") || party&.[]("name")
      end

      def occurred_at(body)
        Time.zone.parse(body.fetch("issued_at").to_s)
      rescue ArgumentError, TypeError
        Time.current
      end

      def canonical_hash(body)
        "sha256:#{Digest::SHA256.hexdigest(JSON.generate(canonicalize(body)))}"
      end

      def canonicalize(value)
        case value
        when Hash
          value.keys.sort.each_with_object({}) { |key, memo| memo[key] = canonicalize(value[key]) }
        when Array
          value.map { |item| canonicalize(item) }
        else
          value
        end
      end

      def advance_loan_case!(body)
        next_status = status_for(body.dig("operation", "name"))
        return unless next_status
        return if LoanCase::STATE_SEQUENCE.index(next_status) < LoanCase::STATE_SEQUENCE.index(@loan_case.status)

        @loan_case.update!(status: next_status)
      end

      def status_for(operation_name)
        {
          "consent.granted" => "intake_complete",
          "kyb.verified" => "intake_complete",
          "documents.received" => "documents_received",
          "cashflow.analysis_completed" => "ai_extraction_complete",
          "ai.recommendation_generated" => "credit_analysis_complete",
          "human_credit_review.completed" => "human_review_complete",
          "loan.application_decisioned" => "conditional_approval_issued",
          "conditional_approval_notice.generated" => "conditional_approval_issued"
        }[operation_name]
      end
    end
  end
end
