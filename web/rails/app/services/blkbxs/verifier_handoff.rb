require "cgi"

module Blkbxs
  module VerifierHandoff
    VERIFY_PAGE_PATH = "/verify/index.html".freeze
    ARTIFACT_PATH = "/api/v1/blkbxs/verifier_artifacts".freeze
    UNAVAILABLE_REASON = "PORTABLE_RECEIPT_MISSING".freeze

    module_function

    def artifact_url(workspace_id:, business_process_id: nil, bundle_id: nil, receipt_id: nil)
      query = {
        workspace_id: workspace_id,
        business_process_id: business_process_id,
        bundle_id: bundle_id,
        receipt_id: receipt_id
      }.compact.to_query
      "#{ARTIFACT_PATH}?#{query}"
    end

    def verify_path(workspace_id:, business_process_id: nil, bundle_id: nil, receipt_id: nil)
      artifact = artifact_url(
        workspace_id: workspace_id,
        business_process_id: business_process_id,
        bundle_id: bundle_id,
        receipt_id: receipt_id
      )
      "#{VERIFY_PAGE_PATH}?artifact_url=#{CGI.escape(artifact)}"
    end

    def payload(workspace:, business_process_id: nil, bundle_id: nil, receipt_id: nil)
      VerifierArtifacts.call(
        workspace: workspace,
        business_process_id: business_process_id,
        bundle_id: bundle_id,
        receipt_id: receipt_id
      )

      {
        "product" => "blkbxs",
        "available" => true,
        "verify_path" => verify_path(
          workspace_id: workspace.id,
          business_process_id: business_process_id,
          bundle_id: bundle_id,
          receipt_id: receipt_id
        ),
        "artifact_url" => artifact_url(
          workspace_id: workspace.id,
          business_process_id: business_process_id,
          bundle_id: bundle_id,
          receipt_id: receipt_id
        )
      }
    rescue ActiveRecord::RecordNotFound
      {
        "product" => "blkbxs",
        "available" => false,
        "reason_code" => UNAVAILABLE_REASON
      }
    end
  end
end
