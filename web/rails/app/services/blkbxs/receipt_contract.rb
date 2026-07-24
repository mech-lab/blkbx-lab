module Blkbxs
  class ReceiptContract
    REQUIRED_FIELDS = %w[
      id
      type
      version
      profile
      issued_at
      operation
      parties
      authority
      state_transition
      evidence
      compliance
      links
      verification
    ].freeze

    def self.ubr_event(body:, domain_metadata: {})
      new(body: body, domain_metadata: domain_metadata).ubr_event
    end

    def self.domain_metadata_for(body:, domain_metadata: {})
      new(body: body, domain_metadata: domain_metadata).domain_metadata
    end

    def initialize(body:, domain_metadata:)
      @body = (body || {}).deep_stringify_keys
      @domain_metadata = (domain_metadata || {}).deep_stringify_keys
    end

    def ubr_event
      validate_required_fields!
      validate_operation!
      validate_links!
      @body
    end

    def domain_metadata
      body = ubr_event
      operation = body.fetch("operation")
      state_subject = body.fetch("state_transition").fetch("subject", {})
      external_reference = operation.fetch("external_reference", {})
      @domain_metadata.merge(
        "business_process_id" => operation.fetch("business_process_id"),
        "application_id" => external_reference["bank_application_id"] || state_subject["id"],
        "ubr_receipt_id" => body.fetch("id"),
        "operation_name" => operation.fetch("name"),
        "operation_phase" => operation.fetch("phase"),
        "bundle_id" => body.dig("links", "bundle_id")
      ).compact
    end

    private

    def validate_required_fields!
      missing = REQUIRED_FIELDS.select { |field| blank?(@body[field]) }
      raise ArgumentError, "UBR receipt is missing required fields: #{missing.join(', ')}" if missing.any?
      raise ArgumentError, "UBR receipt type must be UniversalBankingReceipt" unless @body["type"] == "UniversalBankingReceipt"
    end

    def validate_operation!
      operation = @body.fetch("operation")
      required = %w[domain name phase action status business_process_id]
      missing = required.select { |field| blank?(operation[field]) }
      raise ArgumentError, "UBR operation is missing required fields: #{missing.join(', ')}" if missing.any?
    end

    def validate_links!
      links = @body.fetch("links")
      raise ArgumentError, "UBR links.parent_receipts must be an array" unless links["parent_receipts"].is_a?(Array)
      raise ArgumentError, "UBR links.bundle_id is required" if blank?(links["bundle_id"])
    end

    def blank?(value)
      value.nil? || value == "" || value == []
    end
  end
end
