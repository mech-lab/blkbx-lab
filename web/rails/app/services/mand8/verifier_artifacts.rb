module Mand8
  class VerifierArtifacts
    def self.call(workspace:, case_id: nil, bundle_id: nil, receipt_id: nil)
      new(workspace: workspace, case_id: case_id, bundle_id: bundle_id, receipt_id: receipt_id).call
    end

    def initialize(workspace:, case_id:, bundle_id:, receipt_id:)
      @workspace = workspace
      @case_id = case_id.presence
      @bundle_id = bundle_id.presence
      @receipt_id = receipt_id.presence
    end

    def call
      bundle = selected_bundle
      context_receipt = selected_receipt(bundle)
      ensure_handoff_context!(receipt: context_receipt, bundle: bundle)

      portable_receipt = selected_portable_receipt(bundle: bundle, context_receipt: context_receipt)
      raise ActiveRecord::RecordNotFound, "No linked portable ink.receipt.v2 found for verifier handoff" unless portable_receipt

      resolved_case_id = resolve_case_id(context_receipt || portable_receipt, bundle)
      policy = selected_policy(portable_receipt)
      registry = selected_registry(policy, portable_receipt)
      revocations = selected_revocations(portable_receipt)
      manifest = selected_manifest(bundle: bundle, portable_receipt: portable_receipt)

      {
        "receipt" => portable_receipt.portable_receipt,
        "manifest" => manifest,
        "verification_policy" => valid_policy_json?(policy&.policy_json) ? policy.policy_json : nil,
        "trust_registry" => registry,
        "revocations" => revocations,
        "reviewer_packet" => reviewer_packet_manifest(
          manifest: manifest,
          policy: policy,
          registry: registry,
          revocations: revocations,
          bundle: bundle,
          case_id: resolved_case_id
        ),
        "context" => {
          "product" => "mand8",
          "workspace_id" => @workspace.id,
          "case_id" => resolved_case_id,
          "bundle_id" => bundle&.id,
          "receipt_id" => portable_receipt.id,
          "linked_receipt_id" => context_receipt&.id,
          "linked_receipt_schema" => context_receipt&.schema_key,
          "linked_bundle_type" => bundle&.bundle_type,
          "title" => context_title(bundle: bundle, case_id: resolved_case_id),
          "signing_key_identifier" => portable_receipt.signing_key_identifier,
          "trust_registry_version" => portable_receipt.trust_registry_version,
          "revocation_version" => portable_receipt.revocation_version
        }.compact
      }
    end

    private

    def selected_bundle
      return @selected_bundle if defined?(@selected_bundle)

      @selected_bundle = if @bundle_id
        @workspace.evidence_bundles.find(@bundle_id)
      elsif @case_id
        @workspace.evidence_bundles.detect { |record| record.manifest["case_id"] == @case_id }
      elsif @receipt_id
        @workspace.evidence_bundles.joins(:receipts).where(receipts: { id: @receipt_id }).order(created_at: :desc).first
      elsif @workspace.metadata["seeded_case_id"].present?
        @workspace.evidence_bundles.detect { |record| record.manifest["case_id"] == @workspace.metadata["seeded_case_id"] }
      else
        @workspace.evidence_bundles.order(created_at: :desc).first
      end
    end

    def selected_receipt(bundle)
      return @selected_receipt if defined?(@selected_receipt)

      @selected_receipt = if @receipt_id
        @workspace.receipts.find(@receipt_id)
      elsif @case_id
        primary_receipt_for_case(@case_id)
      elsif bundle.present?
        rank_receipts(bundle.receipts).first
      elsif @workspace.metadata["seeded_case_id"].present?
        primary_receipt_for_case(@workspace.metadata["seeded_case_id"])
      else
        rank_receipts(@workspace.receipts.order(created_at: :desc)).first
      end
    end

    def selected_portable_receipt(bundle:, context_receipt:)
      return context_receipt if portable_receipt?(context_receipt)

      resolved_case_id = resolve_case_id(context_receipt, bundle)

      if bundle.present?
        portable = newest_portable_receipt(bundle.receipts)
        return portable if portable.present?
      end

      if resolved_case_id.present?
        portable = newest_portable_receipt(
          @workspace.receipts.select do |record|
            portable_receipt?(record) && WorkspaceSnapshot.case_id_for_receipt(record) == resolved_case_id
          end
        )
        return portable if portable.present?
      end

      return nil if @case_id.present? || @bundle_id.present? || @receipt_id.present?

      newest_portable_receipt(@workspace.receipts.order(created_at: :desc))
    end

    def selected_policy(receipt)
      receipt&.verification_runs&.recent&.first&.verification_policy ||
        @workspace.verification_policies.active.order(:id).first
    end

    def selected_registry(policy, portable_receipt)
      published = publication_json("trust_registry", portable_receipt.trust_registry_version)
      return published if valid_registry_json?(published)

      registry = policy&.trust_registry || @workspace.trust_registries.active.order(:id).first
      registry&.registry_json if valid_registry_json?(registry&.registry_json)
    end

    def selected_revocations(portable_receipt)
      publication_json("revocations", portable_receipt.revocation_version)
    end

    def reviewer_packet_manifest(manifest:, policy:, registry:, revocations:, bundle:, case_id:)
      {
        "schema" => "mand8.reviewer_packet.v1",
        "profile" => "mand8.procurement_reviewer_packet",
        "case_id" => case_id,
        "bundle_id" => bundle&.id,
        "files" => {
          "receipt" => "ink_receipt.v2.json",
          "manifest" => manifest.present? ? "ink_manifest.v2.json" : nil,
          "verification_policy" => valid_policy_json?(policy&.policy_json) ? "verify-policy.json" : nil,
          "trust_registry" => registry.present? ? "trust-registry.json" : nil,
          "revocations" => revocations.present? ? "revocations.json" : nil
        }.compact,
        "instructions" => [
          "Verify locally with the native Rust verifier; do not rely on the hosted dashboard as the trust root.",
          "Use the browser/WASM verifier only as a parity surface over the same packet artifacts.",
          "Compare reviewer results against test-vectors/ink-vectors.json before accepting a release packet."
        ],
        "native_verify_command" => native_verify_command(
          manifest: manifest,
          policy: policy,
          registry: registry,
          revocations: revocations
        ),
        "vector_corpus" => "test-vectors/ink-vectors.json"
      }
    end

    def native_verify_command(manifest:, policy:, registry:, revocations:)
      [
        "ink receipt",
        "--receipt ink_receipt.v2.json",
        ("--manifest ink_manifest.v2.json" if manifest.present?),
        ("--policy verify-policy.json" if valid_policy_json?(policy&.policy_json)),
        ("--trust-registry trust-registry.json" if registry.present?),
        ("--revocation-list revocations.json" if revocations.present?)
      ].compact.join(" ")
    end

    def resolve_case_id(receipt, bundle)
      @case_id ||
        WorkspaceSnapshot.case_id_for_receipt(receipt) ||
        bundle&.manifest&.[]("case_id") ||
        @workspace.metadata["seeded_case_id"] ||
        @workspace.receipts.filter_map { |record| WorkspaceSnapshot.case_id_for_receipt(record) }.uniq.sort.first
    end

    def primary_receipt_for_case(case_id)
      rank_receipts(
        @workspace.receipts.select { |record| WorkspaceSnapshot.case_id_for_receipt(record) == case_id }
      ).first
    end

    def rank_receipts(scope)
      Array(scope).sort_by do |record|
        [
          case record.schema_key
          when WorkspaceSnapshot::RISK_SCHEMA then 0
          when WorkspaceSnapshot::AUTHORITY_SCHEMA then 1
          when WorkspaceSnapshot::INCIDENT_SCHEMA then 2
          else 3
          end,
          record.created_at || Time.at(0)
        ]
      end
    end

    def ensure_handoff_context!(receipt:, bundle:)
      return if receipt.present? || bundle.present?

      raise ActiveRecord::RecordNotFound, "No linked MAND8 artifacts found for verifier handoff"
    end

    def selected_manifest(bundle:, portable_receipt:)
      return bundle.manifest if portable_manifest?(bundle&.manifest)

      portable_receipt.evidence_bundles.order(created_at: :desc).map(&:manifest).find do |manifest|
        portable_manifest?(manifest)
      end
    end

    def newest_portable_receipt(scope)
      Array(scope)
        .select { |record| portable_receipt?(record) }
        .max_by { |record| record.created_at || Time.at(0) }
    end

    def portable_receipt?(receipt)
      receipt&.portable_receipt.present?
    end

    def portable_manifest?(manifest)
      manifest.is_a?(Hash) && manifest["schema"] == "ink.manifest.v2"
    end

    def valid_policy_json?(document)
      document.is_a?(Hash) && document["schema"] == "ink.verify-policy.v1"
    end

    def valid_registry_json?(document)
      document.is_a?(Hash) && %w[ink.trust-registry.v1 ink.trust-registry.v2].include?(document["schema"])
    end

    def publication_json(artifact_kind, version)
      scope = @workspace.trust_publications.where(artifact_kind: artifact_kind)
      scope = scope.where(version: version) if version.present?
      scope.current_first.first&.artifact_json
    end

    def context_title(bundle:, case_id:)
      return bundle.title if bundle&.title.present?
      return "MAND8 verifier handoff for #{case_id}" if case_id.present?

      "MAND8 verifier handoff"
    end
  end
end
