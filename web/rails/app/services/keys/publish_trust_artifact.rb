require "digest"
require "json"

module Keys
  class PublishTrustArtifact
    def self.call(ceremony:, artifact_kind:, version:, artifact_json: nil, artifact_url: nil)
      new(
        ceremony: ceremony,
        artifact_kind: artifact_kind,
        version: version,
        artifact_json: artifact_json,
        artifact_url: artifact_url
      ).call
    end

    def initialize(ceremony:, artifact_kind:, version:, artifact_json:, artifact_url:)
      @ceremony = ceremony
      @artifact_kind = artifact_kind
      @version = version
      @artifact_json = artifact_json
      @artifact_url = artifact_url
    end

    def call
      raise ArgumentError, "approval quorum not satisfied" unless @ceremony.approval_quorum_met?

      payload = @artifact_json.presence || generated_artifact
      state = payload.dig("signing", "signature").present? ? "published" : "pending_signature"

      publication = TrustPublication.create!(
        organization: @ceremony.organization,
        workspace: @ceremony.workspace,
        key_ceremony: @ceremony,
        signing_key: @ceremony.signing_key,
        artifact_kind: @artifact_kind,
        version: @version,
        state: state,
        artifact_url: @artifact_url,
        artifact_json: payload,
        published_at: Time.current
      )
      @ceremony.update!(state: "published", executed_at: Time.current)
      publication
    end

    private

    def generated_artifact
      case @artifact_kind
      when "trust_registry"
        trust_registry_payload
      when "revocations"
        revocations_payload
      else
        raise ArgumentError, "unsupported artifact kind #{@artifact_kind}"
      end
    end

    def trust_registry_payload
      timestamp = Time.current.utc.iso8601
      signing_key = trust_authority_key
      issuers = @ceremony.organization.signing_keys.order(:created_at).map do |key|
        {
          key_id: key.key_identifier,
          algorithm: key.key_type,
          public_key: key.public_key,
          issuer_name: key.issuer&.name || "Platform Issuer",
          org_name: @ceremony.organization.name,
          usage: key.usage,
          state: key.state,
          valid_from: (key.activated_at || key.created_at || Time.current).utc.iso8601,
          valid_until: key.retired_at&.utc&.iso8601
        }
      end
      payload = {
        schema: "ink.trust-registry.v2",
        registry_version: @version,
        published_at: timestamp,
        trust_authorities: Array(signing_key).map do |key|
          {
            key_id: key.key_identifier,
            algorithm: key.key_type,
            public_key: key.public_key,
            state: key.state == "revoked" ? "revoked" : "active"
          }
        end,
        issuers: issuers
      }
      signing_payload(payload, signing_key&.key_identifier, "INK-TRUST-REGISTRY-JSON-V2")
    end

    def revocations_payload
      timestamp = Time.current.utc.iso8601
      signing_key = trust_authority_key
      revoked = @ceremony.organization.signing_keys.where(state: "revoked").order(:updated_at).map do |key|
        {
          key_id: key.key_identifier,
          reason: key.metadata["revocation_reason"].presence || "revoked_by_ceremony",
          revoked_at: (key.revoked_at || key.updated_at || Time.current).utc.iso8601
        }
      end
      payload = {
        schema: "ink.revocations.v2",
        list_version: @version,
        published_at: timestamp,
        revoked_keys: revoked
      }
      signing_payload(payload, signing_key&.key_identifier, "INK-REVOCATION-JSON-V2")
    end

    def signing_payload(payload, key_id, transcript_encoding)
      digest = Digest::SHA256.hexdigest(JSON.generate(deep_sort(payload)))
      payload.merge(
        signing: {
          transcript_encoding: transcript_encoding,
          payload_hash: {
            algorithm: "sha-256",
            digest: digest
          },
          algorithm: "Ed25519",
          key_id: key_id,
          signature: nil
        }
      )
    end

    def trust_authority_key
      @ceremony.organization.signing_keys.trust_publication.active.order(:id).first
    end

    def deep_sort(value)
      case value
      when Hash
        value.keys.sort.each_with_object({}) { |key, memo| memo[key] = deep_sort(value[key]) }
      when Array
        value.map { |item| deep_sort(item) }
      else
        value
      end
    end
  end
end
