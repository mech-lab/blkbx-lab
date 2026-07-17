module Ink
  class BuildBundle
    def self.call(options = {})
      new(options).call
    end

    def initialize(options = {})
      @organization = options.fetch(:organization)
      @workspace = options.fetch(:workspace)
      @bundle_type = options.fetch(:bundle_type)
      @title = options.fetch(:title)
      @receipts = Array(options.fetch(:receipts))
      @actor = options[:actor]
      @workflow_run = options[:workflow_run]
    end

    def call
      bundle = EvidenceBundle.create!(
        organization: @organization,
        workspace: @workspace,
        workflow_run: @workflow_run,
        created_by: @actor,
        bundle_type: @bundle_type,
        title: @title,
        status: "draft"
      )

      @receipts.each do |receipt|
        artifact = receipt.evidence_artifacts.first_or_create!(
          organization: @organization,
          workspace: @workspace,
          artifact_kind: "receipt_evidence",
          content_type: "application/json",
          byte_size: JSON.generate(receipt.body_json).bytesize,
          sha256: receipt.sha256,
          metadata: { receipt_id: receipt.id }
        ) do |record|
          record.storage_key = StorageKeyBuilder.call(kind: :artifact, organization_id: @organization.id, record_id: receipt.id, filename: "evidence.json")
        end

        EvidenceBundleArtifact.create!(
          organization: @organization,
          workspace: @workspace,
          evidence_bundle: bundle,
          evidence_artifact: artifact
        )
      end

      manifest = {
        bundle_type: @bundle_type,
        title: @title,
        receipt_ids: @receipts.map(&:id),
        verification_policy_ids: @receipts.flat_map { |receipt| receipt.verification_runs.select(:verification_policy_id).pluck(:verification_policy_id) }.uniq
      }
      manifest_json = JSON.generate(manifest)

      bundle.update!(
        manifest: manifest,
        storage_key: StorageKeyBuilder.call(kind: :bundle, organization_id: @organization.id, record_id: bundle.id, filename: "bundle.zip"),
        sha256: Digest::SHA256.hexdigest(manifest_json),
        status: "ready"
      )

      UsageEvent.track("bundle.created", organization: @organization, workspace: @workspace, metadata: { evidence_bundle_id: bundle.id, bundle_type: @bundle_type })
      AuditEvent.record!("bundle.created", auditable: bundle, organization: @organization, workspace: @workspace, user: @actor, request_id: Current.request_id, resulting_state: bundle.attributes)

      bundle
    end
  end
end
