module Mand8
  class BuildRenewalBundle
    def self.call(organization:, workspace:, actor: nil, receipts:, title: "Renewal evidence bundle", workflow_run: nil)
      bundle = Ink::BuildBundle.call(
        organization: organization,
        workspace: workspace,
        actor: actor,
        receipts: receipts,
        title: title,
        workflow_run: workflow_run,
        bundle_type: "mand8_renewal"
      )
      case_ids = Array(receipts).map { |receipt| WorkspaceSnapshot.case_id_for_receipt(receipt) }.compact.uniq
      raise ArgumentError, "MAND8 renewal bundles require at least one case-linked receipt" if case_ids.empty?
      raise ArgumentError, "MAND8 renewal bundles require receipts from a single case" if case_ids.size > 1

      snapshot = WorkspaceSnapshot.case_summary_for_bundle(bundle, case_id: case_ids.first)
      updated_manifest = bundle.manifest.merge(
          "case_id" => case_ids.first,
          "product_type" => "mand8",
          "underwriter_summary" => snapshot.slice(
            "case_id",
            "policy_ref",
            "binder_ref",
            "authority_status",
            "human_review_status",
            "incident_count",
            "latest_incident_severity",
            "renewal_ready",
            "latest_verification_status"
          ),
          "receipt_summaries" => snapshot.fetch("receipts"),
          "verifier_handoff" => VerifierHandoff.payload(
            workspace: workspace,
            case_id: case_ids.first,
            bundle_id: bundle.id
          )
        )
      bundle.update!(
        manifest: updated_manifest,
        sha256: Digest::SHA256.hexdigest(JSON.generate(updated_manifest))
      )
      bundle
    end
  end
end
