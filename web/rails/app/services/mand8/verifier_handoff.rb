require "cgi"

module Mand8
  module VerifierHandoff
    VERIFY_PAGE_PATH = "/verify/index.html".freeze
    ARTIFACT_PATH = "/api/v1/mand8/verifier_artifacts".freeze
    UNAVAILABLE_REASON = "PORTABLE_RECEIPT_MISSING".freeze

    module_function

    def artifact_url(workspace_id:, case_id: nil, bundle_id: nil, receipt_id: nil)
      query = {
        workspace_id: workspace_id,
        case_id: case_id,
        bundle_id: bundle_id,
        receipt_id: receipt_id
      }.compact.to_query
      "#{ARTIFACT_PATH}?#{query}"
    end

    def verify_path(workspace_id:, case_id: nil, bundle_id: nil, receipt_id: nil)
      artifact = artifact_url(
        workspace_id: workspace_id,
        case_id: case_id,
        bundle_id: bundle_id,
        receipt_id: receipt_id
      )
      "#{VERIFY_PAGE_PATH}?artifact_url=#{CGI.escape(artifact)}"
    end

    def payload(workspace:, case_id: nil, bundle_id: nil, receipt_id: nil)
      ::Mand8::VerifierArtifacts.call(
        workspace: workspace,
        case_id: case_id,
        bundle_id: bundle_id,
        receipt_id: receipt_id
      )

      {
        "product" => "mand8",
        "available" => true,
        "verify_path" => verify_path(
          workspace_id: workspace.id,
          case_id: case_id,
          bundle_id: bundle_id,
          receipt_id: receipt_id
        ),
        "artifact_url" => artifact_url(
          workspace_id: workspace.id,
          case_id: case_id,
          bundle_id: bundle_id,
          receipt_id: receipt_id
        )
      }
    rescue ActiveRecord::RecordNotFound
      {
        "product" => "mand8",
        "available" => false,
        "reason_code" => UNAVAILABLE_REASON
      }
    end
  end
end
