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
  end
end
