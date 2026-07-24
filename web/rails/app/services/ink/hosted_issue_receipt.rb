require "json"
require "net/http"
require "uri"

module Ink
  class HostedIssueReceipt
    def self.enabled?
      ENV["INK_ISSUER_SERVICE_URL"].present?
    end

    def self.call(receipt:)
      new(receipt: receipt).call
    end

    def initialize(receipt:)
      @receipt = receipt
    end

    def call
      return @receipt unless self.class.enabled?

      uri = URI.parse("#{base_url}/v1/receipts/issue")
      request = Net::HTTP::Post.new(uri)
      request["Content-Type"] = "application/json"
      request["Authorization"] = "Bearer #{bearer_token}" if bearer_token.present?
      request.body = JSON.generate(payload)

      response = http_client(uri) { |http| http.request(request) }
      unless response.is_a?(Net::HTTPSuccess)
        raise StandardError, "issuer service returned #{response.code}: #{response.body}"
      end

      parsed = JSON.parse(response.body)
      @receipt.update!(
        portable_receipt_json: parsed.fetch("receipt"),
        signing_key_identifier: parsed["key_id"],
        trust_registry_version: parsed["trust_registry_version"],
        revocation_version: parsed["revocation_version"],
        signer_request_id: parsed["signer_request_id"]
      )
      persist_portable_manifest!(parsed["manifest"]) if portable_manifest?(parsed["manifest"])
      @receipt
    end

    private

    def payload
      {
        receipt_id: "urn:ink:receipt:rails:#{@receipt.id}",
        action_id: action_id,
        workflow_kind: @receipt.workflow_kind.presence || "ink_generic",
        schema_key: @receipt.schema_key,
        schema_version: @receipt.schema_version,
        body_json: @receipt.body_json,
        domain_metadata: @receipt.domain_metadata,
        decision: @receipt.domain_metadata["decision"] || @receipt.body_json["decision"],
        issued_at: @receipt.issued_at&.to_i,
        policy_id: "rails_workflow_policy",
        policy_version: "1.0.0"
      }
    end

    def action_id
      @receipt.domain_metadata["action_id"].presence ||
        @receipt.body_json["action_id"].presence ||
        "urn:ink:action:rails:#{@receipt.id}"
    end

    def base_url
      ENV.fetch("INK_ISSUER_SERVICE_URL").delete_suffix("/")
    end

    def bearer_token
      ENV["INK_ISSUER_SERVICE_TOKEN"]
    end

    def http_client(uri, &block)
      Net::HTTP.start(
        uri.host,
        uri.port,
        use_ssl: uri.scheme == "https",
        read_timeout: ENV.fetch("INK_ISSUER_SERVICE_TIMEOUT_SECONDS", 5).to_i,
        &block
      )
    end

    def persist_portable_manifest!(manifest)
      bundle = EvidenceBundle.where(
        organization: @receipt.organization,
        workspace: @receipt.workspace,
        bundle_type: "portable_companion",
        title: portable_bundle_title
      ).first_or_initialize

      manifest_json = JSON.generate(manifest)
      bundle.assign_attributes(
        manifest: manifest,
        status: "ready",
        storage_key: StorageKeyBuilder.call(kind: :bundle, organization_id: @receipt.organization_id, record_id: @receipt.id, filename: "portable-verifier-packet.zip"),
        sha256: Digest::SHA256.hexdigest(manifest_json)
      )
      bundle.save!

      link_packet_artifact!(bundle, "portable_receipt", "ink_receipt.v2.json", @receipt.portable_receipt)
      link_packet_artifact!(bundle, "portable_manifest", "ink_manifest.v2.json", manifest)
    end

    def link_packet_artifact!(bundle, artifact_kind, filename, payload)
      payload_json = JSON.generate(payload)
      artifact = EvidenceArtifact.where(
        storage_key: StorageKeyBuilder.call(kind: :artifact, organization_id: @receipt.organization_id, record_id: @receipt.id, filename: filename)
      ).first_or_initialize
      artifact.assign_attributes(
        organization: @receipt.organization,
        workspace: @receipt.workspace,
        receipt: @receipt,
        artifact_kind: artifact_kind,
        content_type: "application/json",
        byte_size: payload_json.bytesize,
        sha256: Digest::SHA256.hexdigest(payload_json),
        metadata: {
          "receipt_id" => @receipt.id,
          "schema" => payload["schema"]
        }.compact
      )
      artifact.save!

      EvidenceBundleArtifact.find_or_create_by!(
        organization: @receipt.organization,
        workspace: @receipt.workspace,
        evidence_bundle: bundle,
        evidence_artifact: artifact
      )
    end

    def portable_manifest?(document)
      document.is_a?(Hash) && document["schema"] == "ink.manifest.v2"
    end

    def portable_bundle_title
      "Portable verifier packet for #{@receipt.external_id.presence || @receipt.id}"
    end
  end
end
