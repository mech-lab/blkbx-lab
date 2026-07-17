require "digest"
require "json"
require "securerandom"

module Mand8
  class ReceiptContract
    DEFAULT_TERRITORY = "UK".freeze
    DEFAULT_MARKET_SEGMENT = "lloyds_delegated_authority".freeze

    def self.insurability(body:, domain_metadata: {})
      new(body: body, domain_metadata: domain_metadata).insurability
    end

    def self.authority(body:, domain_metadata: {})
      new(body: body, domain_metadata: domain_metadata).authority
    end

    def self.incident(body:, domain_metadata: {})
      new(body: body, domain_metadata: domain_metadata).incident
    end

    def initialize(body:, domain_metadata:)
      @body = (body || {}).deep_stringify_keys
      @domain_metadata = (domain_metadata || {}).deep_stringify_keys
    end

    def insurability
      context = base_domain_context.merge(@body.fetch("domain_context", {}))
      document = {
        "schema" => "mand8.risk_receipt.v1",
        "receipt_id" => @body["receipt_id"].presence || new_identifier("rcpt"),
        "action_id" => @body["action_id"].presence || new_identifier("act"),
        "case_id" => resolved_case_id,
        "issued_at" => resolved_issued_at,
        "domain_context" => context,
        "event_trail" => normalized_event_trail(
          @body["event_trail"],
          default: [
            {
              "event_type" => "underwriting_action_emitted",
              "payload" => {
                "action" => @body["action"].presence || "ai_underwriting_action",
                "decision" => @body["decision"].presence || "bind_with_controls",
                "exposure_unit_id" => context["exposure_unit_id"],
                "policy_ref" => context["policy_ref"]
              }
            }
          ]
        ),
        "human_review" => normalized_human_review(@body["human_review"]),
      }
      with_integrity(document)
    end

    def authority
      context = {
        "case_id" => resolved_case_id,
        "policy_ref" => pick("policy_ref"),
        "binder_ref" => pick("binder_ref"),
        "lloyds_binding_ref" => pick("lloyds_binding_ref") || pick("binder_ref"),
        "territory" => pick("territory") || DEFAULT_TERRITORY,
        "market_segment" => pick("market_segment") || DEFAULT_MARKET_SEGMENT,
        "managing_agent" => pick("managing_agent"),
        "coverholder" => pick("coverholder"),
        "regulators" => Array(pick("regulators")).presence || %w[FCA PRA]
      }.compact
      document = {
        "schema" => "mand8.authority_receipt.v1",
        "receipt_id" => @body["receipt_id"].presence || new_identifier("arcpt"),
        "action_id" => @body["action_id"].presence || new_identifier("act"),
        "case_id" => resolved_case_id,
        "issued_at" => resolved_issued_at,
        "domain_context" => context,
        "authority_scope" => {
          "authority_id" => pick("authority_id"),
          "construct" => pick("construct") || "delegated_authority",
          "status" => pick("status") || "within_authority",
          "delegated_authority" => @body.fetch("delegated_authority", true),
          "permitted_risk_classes" => Array(pick("permitted_risk_classes")),
          "controls_required" => Array(pick("controls_required")),
          "policy_conditions" => Array(pick("policy_conditions")),
          "exclusions" => Array(pick("exclusions")),
          "authority_notes" => pick("authority_notes")
        }.compact,
        "event_trail" => normalized_event_trail(
          @body["event_trail"],
          default: [
            {
              "event_type" => "delegated_authority_checked",
              "payload" => {
                "authority_id" => pick("authority_id"),
                "status" => pick("status") || "within_authority",
                "lloyds_binding_ref" => pick("lloyds_binding_ref") || pick("binder_ref")
              }
            }
          ]
        ),
        "human_review" => normalized_human_review(@body["human_review"]),
      }
      with_integrity(document)
    end

    def incident
      {
        "schema" => "mand8.incident_receipt.v1",
        "case_id" => resolved_case_id,
        "incident_id" => @body["incident_id"].presence || new_identifier("inc"),
        "incident_type" => @body["incident_type"].presence || "monitoring_exception",
        "severity" => @body["severity"].presence || "medium",
        "description" => @body["description"].presence || "Incident recorded for delegated-authority review.",
        "claims_impact" => @body["claims_impact"].presence || "monitor_for_renewal",
        "resolution" => (@body["resolution"].presence || {}).deep_stringify_keys
      }
    end

    private

    def resolved_case_id
      @resolved_case_id ||= pick("case_id") || new_identifier("case")
    end

    def resolved_issued_at
      @body["issued_at"].presence || Time.current.utc.iso8601
    end

    def base_domain_context
      {
        "case_id" => resolved_case_id,
        "exposure_unit_id" => pick("exposure_unit_id"),
        "policy_ref" => pick("policy_ref"),
        "risk_class" => pick("risk_class"),
        "insured_value" => pick("insured_value"),
        "currency" => pick("currency") || "GBP",
        "territory" => pick("territory") || DEFAULT_TERRITORY,
        "market_segment" => pick("market_segment") || DEFAULT_MARKET_SEGMENT,
        "binder_ref" => pick("binder_ref"),
        "lloyds_binding_ref" => pick("lloyds_binding_ref") || pick("binder_ref"),
        "managing_agent" => pick("managing_agent"),
        "coverholder" => pick("coverholder"),
        "policy_conditions" => Array(pick("policy_conditions")),
        "exclusions" => Array(pick("exclusions")),
        "regulators" => Array(pick("regulators")).presence || %w[FCA PRA]
      }.compact
    end

    def normalized_event_trail(events, default:)
      source = Array(events).presence || default
      source.map do |entry|
        event = entry.deep_stringify_keys
        payload = event.fetch("payload", {}).deep_stringify_keys
        payload["case_id"] ||= resolved_case_id
        { "event_type" => event["event_type"], "payload" => payload }
      end
    end

    def normalized_human_review(review)
      source = (review || {}).deep_stringify_keys
      {
        "reviewer" => source["reviewer"],
        "notes" => source["notes"],
        "status" => source["status"].presence || "not_reviewed",
        "reviewed_at" => source["reviewed_at"].presence
      }.tap do |payload|
        payload["reviewed_at"] ||= Time.current.utc.iso8601 if payload["status"] != "not_reviewed"
      end
    end

    def pick(key)
      @body[key].presence ||
        @body.fetch("domain_context", {}).deep_stringify_keys[key].presence ||
        @domain_metadata[key].presence
    end

    def new_identifier(prefix)
      "#{prefix}_#{SecureRandom.hex(6)}"
    end

    def with_integrity(document)
      body_without_integrity = document.deep_dup
      document.merge(
        "integrity" => {
          "digest" => "sha256:#{Digest::SHA256.hexdigest(canonical_json(body_without_integrity))}",
          "signature_algorithm" => "stub-v1",
          "signature" => nil,
          "core_binding" => nil
        }
      )
    end

    def canonical_json(payload)
      JSON.generate(deep_sort(payload))
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
