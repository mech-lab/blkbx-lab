module Blkbxs
  module Sprint
    class BuildEvidenceBundle
      def self.call(options = {})
        new(options).call
      end

      def initialize(options = {})
        @loan_case = options.fetch(:loan_case)
        @actor = options[:actor]
        @title = options[:title] || "BLKBXS SMB $250k Evidence Passport"
      end

      def call
        receipts = @loan_case.receipts.to_a
        raise ArgumentError, "BLKBXS sprint evidence bundle requires signed UBR receipts" if receipts.empty?

        bundle = Blkbxs::BuildUbrBundle.call(
          organization: @loan_case.organization,
          workspace: @loan_case.workspace,
          actor: @actor,
          receipts: receipts,
          title: @title,
          evidence_manifest: fixture.fetch("evidence_manifest"),
          verifier_report: fixture.fetch("verifier_report")
        )

        manifest = bundle.manifest.merge(
          "loan_case_id" => @loan_case.id,
          "case_number" => @loan_case.case_number,
          "scenario_type" => @loan_case.scenario_type,
          "sprint_console" => {
            "name" => "BLKBXS Sprint Console",
            "flow" => "AI-assisted SMB $250,000 conditional approval",
            "fixture_source_path" => DemoCatalog::FIXTURE_PATH.to_s
          }
        )
        bundle.update!(manifest: manifest, sha256: Digest::SHA256.hexdigest(JSON.generate(manifest)))
        @loan_case.update!(status: "evidence_bundle_generated")
        bundle
      end

      private

      def fixture
        @fixture ||= DemoCatalog.fetch(DemoCatalog::CANONICAL_EXTERNAL_SCENARIO)
      end
    end
  end
end
