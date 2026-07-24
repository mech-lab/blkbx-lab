module Blkbxs
  module UbrGraph
    module_function

    def validate(receipts, evidence_manifest: nil, verifier_report: nil)
      records = Array(receipts)
      payloads = records.map { |record| payload_for(record) }
      duplicate_ids = payloads.map { |payload| receipt_id(payload) }.compact.group_by(&:itself).select { |_id, ids| ids.length > 1 }.keys
      by_id = payloads.index_by { |payload| receipt_id(payload) }
      failures = []

      duplicate_ids.sort.each do |duplicate_id|
        failures << failure("duplicate_receipt_id", duplicate_id, "Receipt id #{duplicate_id} appears more than once.")
      end

      payloads.each_with_index do |payload, index|
        ReceiptContract.ubr_event(body: payload)
      rescue ArgumentError => error
        failures << failure("schema_invalid", receipt_id(payload) || index.to_s, error.message)
      end

      process_ids = payloads.map { |payload| business_process_id(payload) }.compact.reject(&:blank?).uniq
      failures << failure("mixed_business_process", nil, "UBR graph contains receipts from multiple business_process_id values.") if process_ids.length > 1

      children = Hash.new { |hash, key| hash[key] = [] }
      indegree = by_id.keys.each_with_object({}) { |key, memo| memo[key] = 0 }
      payloads.each do |payload|
        child_id = receipt_id(payload)
        parent_receipt_ids(payload).each do |parent_id|
          parent = by_id[parent_id]
          unless parent
            failures << failure("missing_parent", child_id, "Parent receipt #{parent_id} is missing.")
            next
          end
          if business_process_id(parent) != business_process_id(payload)
            failures << failure("cross_process_parent", child_id, "Parent receipt #{parent_id} belongs to a different business process.")
            next
          end
          children[parent_id] << child_id
          indegree[child_id] += 1
        end
      end

      queue = indegree.select { |_id, degree| degree.zero? }.keys.sort
      order = []
      until queue.empty?
        current = queue.shift
        order << current
        children[current].sort.each do |child_id|
          indegree[child_id] -= 1
          queue << child_id if indegree[child_id].zero?
        end
      end
      failures << failure("cycle_detected", nil, "UBR graph contains a cycle.") if order.length != by_id.length

      evidence = evidence_summary(payloads, evidence_manifest)
      ai_boundary = ai_boundary_summary(payloads)
      failures.concat(ai_boundary.fetch("failures"))

      report_order = verifier_report&.dig("graph_results", "topological_order")
      if report_order.present? && order.present? && report_order != order
        failures << failure("verifier_report_order_mismatch", nil, "Verifier report topological order does not match the receipt graph.")
      end

      {
        "valid" => failures.empty?,
        "business_process_id" => process_ids.first,
        "receipt_count" => payloads.length,
        "topological_order" => order,
        "root_receipts" => order.select { |receipt_id| parent_receipt_ids(by_id.fetch(receipt_id)).empty? },
        "terminal_receipts" => order.select { |receipt_id| children[receipt_id].empty? },
        "evidence_summary" => evidence,
        "ai_boundary_summary" => ai_boundary,
        "failures" => failures
      }
    end

    def payload_for(record)
      record.respond_to?(:body_json) ? record.body_json : record
    end

    def receipt_id(record_or_payload)
      payload_for(record_or_payload)["id"]
    end

    def business_process_id(record_or_payload)
      payload_for(record_or_payload).dig("operation", "business_process_id")
    end

    def application_id(record_or_payload)
      payload = payload_for(record_or_payload)
      payload.dig("operation", "external_reference", "bank_application_id") ||
        payload.dig("state_transition", "subject", "id")
    end

    def parent_receipt_ids(record_or_payload)
      Array(payload_for(record_or_payload).dig("links", "parent_receipts"))
    end

    def evidence_summary(payloads, evidence_manifest)
      items = Array(evidence_manifest&.dig("evidence"))
      manifest_by_id = items.index_by { |item| item["id"] }
      referenced_ids = payloads.flat_map { |payload| Array(payload["evidence"]).map { |item| item["id"] }.compact }.uniq
      committed_only = items.select { |item| item["available_to_verifier"] == false }
      available = items.select { |item| item["available_to_verifier"] == true }
      {
        "evidence_items" => items.length,
        "referenced_evidence_items" => referenced_ids.length,
        "available_to_verifier" => available.length,
        "committed_only" => committed_only.length,
        "missing" => referenced_ids.reject { |id| manifest_by_id.key?(id) }.sort,
        "sensitive_documents_committed_only" => committed_only.map { |item| item["id"] }.compact
      }
    end

    def ai_boundary_summary(payloads)
      ai_receipts = payloads.select { |payload| payload.dig("ai_assistance", "used") == true }
      final_decisions = payloads.select { |payload| payload.dig("operation", "name") == "loan.application_decisioned" }
      human_review_ids = payloads.select { |payload| payload.dig("operation", "name") == "human_credit_review.completed" }.map { |payload| receipt_id(payload) }
      failures = []

      final_decisions.each do |payload|
        controls = payload.dig("ai_assistance", "risk_controls") || {}
        systems = Array(payload.dig("ai_assistance", "systems"))
        human_required = controls["human_review_receipt"].present? ||
          controls["human_approval_required_above_100k"].present? ||
          systems.any? { |system| system["human_review_required"] }
        human_completed = human_review_ids.include?(controls["human_review_receipt"]) ||
          systems.any? { |system| system["human_review_completed"] }
        if human_required && !human_completed
          failures << failure("human_review_missing", receipt_id(payload), "Final loan decision requires completed human review evidence.")
        end
      end

      {
        "valid" => failures.empty?,
        "ai_used" => ai_receipts.any?,
        "ai_receipt_count" => ai_receipts.length,
        "final_decision_count" => final_decisions.length,
        "human_review_receipt_count" => human_review_ids.length,
        "failures" => failures
      }
    end

    def decision_summary(receipts, verifier_report = nil)
      report_decision = verifier_report&.dig("decision")
      return report_decision if report_decision.present?

      payloads = Array(receipts).map { |record| payload_for(record) }
      decision = payloads.find { |payload| payload.dig("operation", "name") == "loan.application_decisioned" } || {}
      after = decision.dig("state_transition", "after") || {}
      {
        "application_id" => application_id(decision),
        "status" => after["application_status"],
        "amount" => after["approved_amount"],
        "term_months" => after["term_months"],
        "apr" => after.dig("interest_rate", "apr") || after["apr"],
        "conditions" => Array(after["conditions"])
      }
    end

    def verifier_report_summary(verifier_report)
      return nil unless verifier_report.present?

      {
        "report_id" => verifier_report["report_id"],
        "generated_at" => verifier_report["generated_at"],
        "summary" => verifier_report["summary"] || {},
        "limitations" => Array(verifier_report["limitations"]),
        "demo_only" => true
      }
    end

    def failure(code, receipt_id, message)
      { "code" => code, "receipt_id" => receipt_id, "message" => message }.compact
    end
  end
end
