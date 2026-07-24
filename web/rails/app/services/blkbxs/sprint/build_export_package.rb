require "csv"
require "digest"
require "fileutils"
require "json"
require "securerandom"
require "zip"

module Blkbxs
  module Sprint
    class BuildExportPackage
      OUTPUT_ROOT = Rails.root.join("tmp", "blkbxs_exports").freeze

      def self.call(options = {})
        new(options).call
      end

      def initialize(options = {})
        @loan_case = options.fetch(:loan_case)
        @actor = options[:actor]
        @package_type = options[:package_type] || "final_bankability_packet"
      end

      def call
        ApplicationRecord.transaction do
          bundle = @loan_case.latest_evidence_bundle || BuildEvidenceBundle.call(loan_case: @loan_case, actor: @actor)
          files = packet_files(bundle)
          zip_path = write_zip(files)
          manifest = package_manifest(bundle, files, zip_path)
          package = @loan_case.export_packages.create!(
            evidence_bundle: bundle,
            package_type: @package_type,
            status: "ready",
            file_path: zip_path.to_s,
            storage_key: "exports/#{@loan_case.organization_id}/#{@loan_case.id}/#{zip_path.basename}",
            sha256: Digest::SHA256.file(zip_path).hexdigest,
            manifest: manifest,
            metadata: {
              "generated_by_user_id" => @actor&.id,
              "generated_at" => Time.current.iso8601
            }.compact
          )
          @loan_case.update!(status: "final_packet_delivered")
          package
        end
      end

      private

      def packet_files(bundle)
        graph = GraphSummary.call(@loan_case)
        claims = BuildClaimsBoundaryMatrix.call(@loan_case)
        exceptions = BuildExceptionRegister.call(@loan_case)

        files = {
          "loan_case.json" => pretty_json(graph.fetch("loan_case")),
          "receipt_graph.json" => pretty_json(graph),
          "verifier_report.json" => pretty_json(bundle.manifest["verifier_report_summary"] || {}),
          "evidence_passport.md" => evidence_passport_markdown(graph, bundle),
          "claims_boundary_matrix.csv" => csv_for(claims, %w[claim_text claim_status evidence_reference limitation]),
          "exception_register.csv" => csv_for(exceptions, %w[severity status title description resolution]),
          "reviewer_objections.csv" => csv_for(reviewer_objections, %w[function severity status objection response]),
          "verify_locally.md" => verify_locally_markdown(graph)
        }

        @loan_case.evidence_events.ordered.each do |event|
          files["events/#{event.external_id.parameterize}.json"] = pretty_json(event.payload)
          if event.receipt
            files["receipts/#{event.external_id.parameterize}.json"] = pretty_json(event.receipt.portable_receipt)
          end
        end

        files["manifest.json"] = pretty_json(packet_manifest_preview(bundle, graph).merge("files" => (files.keys + ["manifest.json"]).sort))
        files
      end

      def package_manifest(bundle, files, zip_path)
        packet_manifest_preview(bundle, GraphSummary.call(@loan_case)).merge(
          "zip" => {
            "path" => zip_path.to_s,
            "sha256" => Digest::SHA256.file(zip_path).hexdigest
          },
          "files" => files.keys.sort
        )
      end

      def packet_manifest_preview(bundle, graph)
        {
          "schema" => "blkbxs.sprint.export_package.v1",
          "product" => "blkbxs",
          "console" => "BLKBXS Sprint Console",
          "flow" => "AI-assisted SMB $250,000 conditional approval",
          "loan_case_id" => @loan_case.id,
          "case_number" => @loan_case.case_number,
          "evidence_bundle_id" => bundle.id,
          "business_process_id" => graph["business_process_id"],
          "portable_receipt_required" => true,
          "trust_root" => "ink.receipt.v2",
          "fixture_provenance" => {
            "source_path" => DemoCatalog::FIXTURE_PATH.to_s,
            "scenario" => DemoCatalog::CANONICAL_EXTERNAL_SCENARIO
          },
          "generated_at" => Time.current.iso8601
        }
      end

      def write_zip(files)
        FileUtils.mkdir_p(OUTPUT_ROOT)
        zip_path = OUTPUT_ROOT.join("#{@loan_case.case_number.parameterize}-#{Time.current.utc.strftime('%Y%m%d%H%M%S')}-#{SecureRandom.hex(4)}.zip")
        Zip::File.open(zip_path, create: true) do |zip|
          files.each do |path, content|
            zip.get_output_stream(path) { |stream| stream.write(content) }
          end
        end
        zip_path
      end

      def pretty_json(value)
        JSON.pretty_generate(value || {})
      end

      def csv_for(rows, headers)
        CSV.generate(headers: true) do |csv|
          csv << headers
          rows.each { |row| csv << headers.map { |header| row[header] } }
        end
      end

      def reviewer_objections
        @loan_case.reviewer_objections.order(:function).map do |objection|
          objection.as_json(only: %i[function severity status objection response])
        end
      end

      def evidence_passport_markdown(graph, bundle)
        <<~MARKDOWN
          # BLKBXS Evidence Passport

          Case: #{@loan_case.case_number}
          Borrower: #{@loan_case.borrower_name}
          Requested amount: $#{@loan_case.requested_amount}
          Bundle: #{bundle.id}
          Receipt count: #{graph["receipt_count"]}
          Signed receipt count: #{graph["signed_receipt_count"]}
          Latest verification status: #{graph["latest_verification_status"] || "not_run"}
          Packet readiness score: #{graph["packet_readiness_score"]}
        MARKDOWN
      end

      def verify_locally_markdown(graph)
        artifact = graph.dig("verifier_handoff", "artifact_url")
        <<~MARKDOWN
          # Verify Locally

          Use the native INK verifier against the linked ink.receipt.v2 artifacts.

          Artifact URL: #{artifact || "not_available"}

          UBR-native demo verifier fields are evidence labels only. The independent trust root is the portable ink.receipt.v2 receipt for each event.
        MARKDOWN
      end
    end
  end
end
