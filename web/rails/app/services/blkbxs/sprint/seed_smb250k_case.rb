module Blkbxs
  module Sprint
    class SeedSmb250kCase
      CASE_NUMBER = "BLKBXS-SMB-250K-001".freeze
      SPRINT_NAME = "BLKBXS SMB $250k Evidence Sprint".freeze

      DEFAULT_OBJECTIONS = [
        ["credit", "Where did DSCR come from?"],
        ["compliance", "Was adverse-action logic preserved?"],
        ["model_risk", "What model produced the recommendation?"],
        ["tprm", "Which vendor touched the workflow?"],
        ["legal", "What does this packet actually prove?"],
        ["audit", "Can we reproduce the chain locally?"],
        ["infosec", "Where are sensitive documents stored?"]
      ].freeze

      def self.call(options = {})
        new(options).call
      end

      def initialize(options = {})
        @organization = options.fetch(:organization)
        @workspace = options.fetch(:workspace)
        @actor = options[:actor]
        @issue_events = options.fetch(:issue_events, false)
      end

      def call
        raise ArgumentError, "workspace product mismatch" unless @workspace.product_type == "blkbxs"

        ApplicationRecord.transaction do
          sprint = seed_sprint!
          loan_case = seed_loan_case!(sprint)
          seed_reviewer_objections!(loan_case)
          events = @issue_events ? seed_events!(loan_case) : loan_case.evidence_events.to_a
          {
            sprint_engagement: sprint,
            loan_case: loan_case.reload,
            evidence_events: events,
            fixture: fixture_summary
          }
        end
      end

      private

      def fixture
        @fixture ||= DemoCatalog.fetch(DemoCatalog::CANONICAL_EXTERNAL_SCENARIO)
      end

      def seed_sprint!
        @workspace.blkbxs_sprint_engagements.where(name: SPRINT_NAME).first_or_initialize.tap do |sprint|
          sprint.assign_attributes(
            organization: @organization,
            status: "active",
            starts_on: Date.current,
            ends_on: 75.days.from_now.to_date,
            metadata: {
              "paid_sprint_offer" => "60-90 Day BLKBXS Evidence Sprint: SMB $250,000 Conditional Approval",
              "source_fixture" => fixture.fetch("fixture_id"),
              "fixture_source_path" => DemoCatalog::FIXTURE_PATH.to_s
            }
          )
          sprint.save!
        end
      end

      def seed_loan_case!(sprint)
        @workspace.blkbxs_loan_cases.where(case_number: CASE_NUMBER).first_or_initialize.tap do |loan_case|
          loan_case.assign_attributes(
            organization: @organization,
            sprint_engagement: sprint,
            status: loan_case.persisted? ? loan_case.status : "draft",
            scenario_type: LoanCase::SCENARIO_TYPE,
            borrower_name: "Sample Main Street Business LLC",
            bank_reviewer_name: "Design Partner Bank Reviewer",
            requested_amount: 250_000,
            metadata: loan_case.metadata.merge(
              "use_of_funds" => "working_capital",
              "ai_assisted" => true,
              "human_review_required" => true,
              "canonical_fixture_id" => fixture.fetch("fixture_id"),
              "source_bundle_sha256" => fixture["source_bundle_sha256"],
              "fixture_borrower_name" => fixture_borrower_name
            ).compact
          )
          loan_case.save!
        end
      end

      def seed_reviewer_objections!(loan_case)
        DEFAULT_OBJECTIONS.each do |function, objection|
          loan_case.reviewer_objections.where(function: function, objection: objection).first_or_create!(
            severity: "medium",
            status: "open",
            metadata: { "seeded" => true }
          )
        end
      end

      def seed_events!(loan_case)
        previous_hash = nil
        fixture.fetch("receipts").each_with_index.map do |body, index|
          event, = BuildEvidenceEvent.call(
            loan_case: loan_case,
            body: body,
            actor: @actor,
            event_order: index + 1,
            previous_event_hash: previous_hash,
            domain_metadata: { "fixture_id" => fixture.fetch("fixture_id") }
          )
          previous_hash = event.canonical_hash
          event
        end
      end

      def fixture_borrower_name
        fixture.fetch("receipts").first.fetch("parties").find { |party| party["role"] == "applicant_business" }&.[]("name")
      end

      def fixture_summary
        {
          "fixture_id" => fixture.fetch("fixture_id"),
          "generated_by" => fixture["generated_by"],
          "source_bundle_sha256" => fixture["source_bundle_sha256"],
          "receipt_count" => fixture.fetch("receipts").length,
          "evidence_count" => fixture.fetch("evidence_manifest").fetch("evidence").length
        }
      end
    end
  end
end
