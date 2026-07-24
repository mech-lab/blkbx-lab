module Mand8
  class ActuarialAnnotation
    SCHEMA_ID = "ink.actuarial_annotation.v1".freeze
    STATUS = "research_unvalidated".freeze
    BADGE = "Research / unvalidated".freeze
    ENGINE_NAME = "blkbx_lab.research.actuarial".freeze
    ENGINE_VERSION = "1.0.0".freeze
    DEFAULT_PROFILE = "mand8_case_v1".freeze
    PASSING_VERIFICATION_STATUSES = %w[valid passed pass warning].freeze
    LIMITATIONS = [
      "Research/unvalidated annotation only.",
      "Does not alter or validate the receipt.",
      "Not a legal, actuarial, insurance, regulatory, reserve, capital, or safety determination.",
      "Evidence penalty is a research observability signal, not a reserve or capital formula."
    ].freeze
    WEIGHTS = {
      "identity" => 0.12,
      "timestamp_sanity" => 0.10,
      "integrity_verification" => 0.18,
      "authority_mapping" => 0.14,
      "human_review" => 0.14,
      "event_trail" => 0.10,
      "controls" => 0.10,
      "incident_exception_transparency" => 0.10,
      "domain_context" => 0.12
    }.freeze

    def self.call(receipts:, verification_reports: [], computed_at: Time.current, profile: DEFAULT_PROFILE)
      new(receipts: receipts, verification_reports: verification_reports, computed_at: computed_at, profile: profile).call
    end

    def initialize(receipts:, verification_reports:, computed_at:, profile:)
      @receipts = Array(receipts).map { |receipt| payload_for(receipt) }
      @verification_reports = Array(verification_reports)
      @computed_at = computed_at
      @profile = profile
    end

    def call
      components, defects = score_components
      completeness_score = weighted_score(components)
      defensibility_score = defensibility_score(completeness_score, defects)
      {
        "schema" => SCHEMA_ID,
        "status" => STATUS,
        "badge" => BADGE,
        "annotates" => {
          "receipt_ids" => receipt_ids,
          "receipt_hashes" => @receipts.map { |receipt| receipt_hash(receipt) },
          "case_id" => case_id
        },
        "engine" => {
          "name" => ENGINE_NAME,
          "version" => ENGINE_VERSION,
          "profile" => @profile
        },
        "computed_at" => timestamp(@computed_at),
        "completeness_score" => completeness_score,
        "defensibility_score" => defensibility_score,
        "evidence_penalty" => (1.0 + (1.0 - defensibility_score)).round(4),
        "components" => components,
        "defects" => defects,
        "limitations" => LIMITATIONS.dup
      }
    end

    private

    def payload_for(receipt)
      payload = receipt.respond_to?(:body_json) ? receipt.body_json : receipt
      JSON.parse(JSON.generate(payload || {}))
    end

    def score_components
      defects = []
      components = {
        "identity" => identity_score(defects),
        "timestamp_sanity" => timestamp_score(defects),
        "integrity_verification" => integrity_verification_score(defects),
        "authority_mapping" => authority_mapping_score(defects),
        "human_review" => human_review_score(defects),
        "event_trail" => event_trail_score(defects),
        "controls" => controls_score(defects),
        "incident_exception_transparency" => incident_exception_score(defects),
        "domain_context" => domain_context_score(defects)
      }
      [components, defects]
    end

    def identity_score(defects)
      return add_defect(defects, "missing_receipt", "critical", "No receipt data was supplied.", "Paper 1") || 0.0 if @receipts.empty?

      total = @receipts.length * 3
      present = @receipts.sum do |receipt|
        [receipt["schema"], receipt["receipt_id"], receipt["action_id"]].count(&:present?)
      end
      score = present.to_f / total
      add_defect(defects, "missing_identity_coordinate", "major", "One or more receipts lack schema, receipt_id, or action_id.", "Paper 2") if score < 1.0
      score
    end

    def timestamp_score(defects)
      return 0.0 if @receipts.empty?

      timestamps = @receipts.map { |receipt| receipt["issued_at"] }
      add_defect(defects, "missing_timestamp", "major", "One or more receipts lack issued_at.", "Paper 2") if timestamps.any?(&:blank?)
      invalid = timestamps.compact.select { |value| parse_time(value).nil? }
      add_defect(defects, "invalid_timestamp", "major", "One or more receipts have an unparsable issued_at.", "Paper 2") if invalid.any?
      timestamps.count { |value| value.present? && parse_time(value).present? }.to_f / @receipts.length
    end

    def integrity_verification_score(defects)
      return 0.0 if @receipts.empty?

      integrity_score = @receipts.count { |receipt| receipt_integrity_digest(receipt).present? }.to_f / @receipts.length
      add_defect(defects, "missing_integrity_digest", "major", "One or more receipts lack an integrity digest.", "Paper 3") if integrity_score < 1.0

      verification_score =
        if @verification_reports.empty?
          add_defect(defects, "missing_verification_report", "moderate", "No external verification report was supplied to the annotation engine.", "Paper 3")
          0.0
        elsif (@verification_reports.map { |report| verification_status(report) } & PASSING_VERIFICATION_STATUSES).any?
          1.0
        else
          add_defect(defects, "failing_verification_report", "critical", "Verification reports did not include a passing status.", "Paper 3")
          0.0
        end
      (integrity_score * 0.65) + (verification_score * 0.35)
    end

    def authority_mapping_score(defects)
      statuses = @receipts.filter_map do |receipt|
        receipt.dig("authority_scope", "status") || receipt.dig("domain_context", "authority_status")
      end
      return 1.0 if statuses.include?("within_authority")

      if statuses.any?
        add_defect(defects, "non_conforming_authority_status", "major", "Authority evidence is present but is not within_authority.", "Paper 2")
        return 0.6
      end
      add_defect(defects, "missing_authority_mapping", "major", "No authority status was found for the case.", "Paper 2")
      0.0
    end

    def human_review_score(defects)
      statuses = @receipts.filter_map { |receipt| receipt.dig("human_review", "status") }
      return 1.0 if statuses.include?("reviewed")

      if statuses.any? { |status| status.present? && status != "not_reviewed" }
        add_defect(defects, "incomplete_human_review", "moderate", "Human review exists but is not marked reviewed.", "Paper 2")
        return 0.5
      end
      add_defect(defects, "absent_human_review", "major", "No reviewed human_review state was found.", "Paper 2")
      0.0
    end

    def event_trail_score(defects)
      return 0.0 if @receipts.empty?

      non_empty = @receipts.count { |receipt| receipt["event_trail"].present? }
      add_defect(defects, "missing_event_trail", "major", "One or more receipts lack an event_trail.", "Paper 3") if non_empty < @receipts.length
      non_empty.to_f / @receipts.length
    end

    def controls_score(defects)
      return 1.0 if @receipts.any? { |receipt| event_count(receipt, "control_check_recorded").positive? }

      add_defect(defects, "missing_control_evidence", "moderate", "No control_check_recorded event was found.", "Paper 5")
      0.0
    end

    def incident_exception_score(defects)
      incident_receipts = @receipts.select { |receipt| receipt["schema"] == "mand8.incident_receipt.v1" }
      incident_events = @receipts.sum { |receipt| event_count(receipt, "incident_recorded") }
      override_events = @receipts.sum { |receipt| event_count(receipt, "override_recorded") }
      context_incident = @receipts.any? { |receipt| receipt.dig("domain_context", "last_incident_id").present? }
      if context_incident && incident_receipts.empty? && incident_events.zero?
        add_defect(defects, "unlinked_incident_context", "moderate", "Incident context exists without a linked incident receipt or event.", "Paper 2")
        return 0.5
      end
      if override_events.positive? && @receipts.none? { |receipt| receipt.dig("human_review", "status") == "reviewed" }
        add_defect(defects, "unreviewed_override", "major", "Override evidence exists without reviewed human review.", "Paper 2")
        return 0.5
      end
      1.0
    end

    def domain_context_score(defects)
      context = @receipts.each_with_object({}) do |receipt, merged|
        merged.merge!(receipt["domain_context"] || {})
      end
      required = %w[case_id policy_ref binder_ref risk_class exposure_unit_id]
      present = required.count { |key| context[key].present? || @receipts.any? { |receipt| receipt[key].present? } }
      score = present.to_f / required.length
      add_defect(defects, "incomplete_domain_context", "moderate", "Domain context lacks one or more expected profile coordinates.", "Paper 1") if score < 1.0
      score
    end

    def weighted_score(components)
      score = WEIGHTS.sum { |name, weight| bounded(components.fetch(name, 0.0)) * weight } / WEIGHTS.values.sum
      bounded(score).round(4)
    end

    def defensibility_score(completeness_score, defects)
      penalties = { "critical" => 0.10, "major" => 0.06, "moderate" => 0.03, "minor" => 0.01 }
      penalty = defects.sum { |defect| penalties.fetch(defect["severity"], 0.01) }
      bounded(completeness_score - penalty).round(4)
    end

    def bounded(value)
      [[value.to_f, 0.0].max, 1.0].min
    end

    def receipt_ids
      @receipts.filter_map { |receipt| receipt["receipt_id"] }
    end

    def receipt_hash(receipt)
      digest = receipt_integrity_digest(receipt)
      return digest if digest.present?

      "sha256:#{Digest::SHA256.hexdigest(JSON.generate(canonicalize(receipt)))}"
    end

    def receipt_integrity_digest(receipt)
      receipt.dig("integrity", "digest")
    end

    def canonicalize(value)
      case value
      when Hash
        value.keys.sort.each_with_object({}) { |key, memo| memo[key] = canonicalize(value[key]) }
      when Array
        value.map { |item| canonicalize(item) }
      else
        value
      end
    end

    def case_id
      @receipts.filter_map { |receipt| receipt["case_id"] || receipt.dig("domain_context", "case_id") }.first
    end

    def event_count(receipt, event_type)
      Array(receipt["event_trail"]).count { |entry| entry["event_type"] == event_type }
    end

    def verification_status(report)
      if report.respond_to?(:status)
        report.status.to_s.downcase
      else
        (report["status"] || report[:status] || report["summary_status"] || report[:summary_status] || report["overall"] || report[:overall] || "unknown").to_s.downcase
      end
    end

    def parse_time(value)
      Time.iso8601(value.to_s)
    rescue ArgumentError
      nil
    end

    def timestamp(value)
      value.respond_to?(:iso8601) ? value.iso8601 : value.to_s
    end

    def add_defect(defects, code, severity, message, source_paper)
      defects << {
        "code" => code,
        "severity" => severity,
        "message" => message,
        "source_paper" => source_paper
      }
      nil
    end
  end
end
