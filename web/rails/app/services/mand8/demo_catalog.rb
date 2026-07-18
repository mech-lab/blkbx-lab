module Mand8
  class DemoCatalog
    SCENARIOS = {
      "lloyds_cyber_happy_path" => {
        "workspace" => {
          "name" => "Lloyd's Cyber Happy Path",
          "slug" => "mand8-lloyds-cyber-happy-path"
        },
        "bundle_title" => "Lloyd's underwriting evidence bundle",
        "risk_receipt" => {
          "case_id" => "case_mand8_lloyds_happy_001",
          "receipt_id" => "rcpt_happy_001",
          "action_id" => "act_happy_001",
          "issued_at" => "2026-07-17T09:00:00Z",
          "decision" => "bind_with_controls",
          "domain_context" => {
            "exposure_unit_id" => "uk-cyber-eu-042",
            "policy_ref" => "B1234UK2026",
            "risk_class" => "cyber",
            "insured_value" => 5_000_000.0,
            "currency" => "GBP",
            "territory" => "UK",
            "market_segment" => "lloyds_delegated_authority",
            "binder_ref" => "B1234UK2026",
            "managing_agent" => "Lime Street Managing Agency Ltd",
            "coverholder" => "North Dock Coverholder Ltd",
            "policy_conditions" => [
              "Quarterly model drift review",
              "Human referral on confidence below threshold"
            ],
            "exclusions" => [
              "Silent cyber outside declared products"
            ],
            "regulators" => %w[FCA PRA]
          },
          "event_trail" => [
            {
              "event_type" => "underwriting_action_emitted",
              "payload" => {
                "action" => "ai_underwriting_action",
                "decision" => "bind_with_controls",
                "exposure_unit_id" => "uk-cyber-eu-042",
                "policy_ref" => "B1234UK2026"
              }
            },
            {
              "event_type" => "control_check_recorded",
              "payload" => {
                "control_id" => "ctl-model-drift-quarterly",
                "control_name" => "Quarterly model drift review",
                "status" => "pass",
                "control_type" => "risk_control",
                "evidence_ref" => "ev-drift-review-q2-2026",
                "details" => { "review_window" => "2026-Q2" }
              }
            },
            {
              "event_type" => "override_recorded",
              "payload" => {
                "override_id" => "ovr-uk-042",
                "override_type" => "no_manual_referral",
                "reason" => "No manual referral required under binder terms.",
                "overridden_by" => "system:no_override",
                "effective_date" => "2026-07-17",
                "outcome" => "not_required",
                "details" => { "confidence_floor_met" => true }
              }
            }
          ],
          "human_review" => {
            "reviewer" => "syndicate.underwriter@mand8.example",
            "notes" => "Delegated authority terms satisfied and London market review complete.",
            "status" => "reviewed",
            "reviewed_at" => "2026-07-17T09:05:00Z"
          }
        },
        "authority_receipts" => [
          {
            "case_id" => "case_mand8_lloyds_happy_001",
            "receipt_id" => "arcpt_happy_001",
            "action_id" => "act_authority_happy_001",
            "issued_at" => "2026-07-17T09:02:00Z",
            "policy_ref" => "B1234UK2026",
            "binder_ref" => "B1234UK2026",
            "lloyds_binding_ref" => "B1234UK2026",
            "authority_id" => "auth-lma-binder-042",
            "managing_agent" => "Lime Street Managing Agency Ltd",
            "coverholder" => "North Dock Coverholder Ltd",
            "permitted_risk_classes" => ["cyber"],
            "controls_required" => ["Quarterly model drift review"],
            "policy_conditions" => ["Human referral on confidence below threshold"],
            "exclusions" => ["Silent cyber outside declared products"],
            "human_review" => {
              "reviewer" => "syndicate.underwriter@mand8.example",
              "notes" => "Delegated authority terms confirmed for the binder.",
              "status" => "reviewed",
              "reviewed_at" => "2026-07-17T09:03:00Z"
            }
          }
        ],
        "incident_receipts" => [],
        "verification_reports" => [
          { "status" => "passed", "report_json" => { "status" => "passed", "details" => "happy_path" } }
        ],
        "review_request" => {
          "title" => "Lloyd's underwriter review",
          "reviewer" => {
            "email" => "underwriter@mand8.example",
            "name" => "Lloyd's Underwriter",
            "role" => "lloyds_underwriter"
          }
        }
      },
      "lloyds_human_review_edge_case" => {
        "workspace" => {
          "name" => "Lloyd's Human Review Edge Case",
          "slug" => "mand8-lloyds-human-review-edge"
        },
        "bundle_title" => "Manual referral review bundle",
        "risk_receipt" => {
          "case_id" => "case_mand8_lloyds_review_002",
          "receipt_id" => "rcpt_review_002",
          "action_id" => "act_review_002",
          "issued_at" => "2026-07-17T10:00:00Z",
          "decision" => "manual_referral_required",
          "domain_context" => {
            "exposure_unit_id" => "uk-cyber-eu-2234",
            "policy_ref" => "B2234UK2026",
            "risk_class" => "cyber",
            "insured_value" => 3_200_000.0,
            "currency" => "GBP",
            "territory" => "UK",
            "market_segment" => "lloyds_delegated_authority",
            "binder_ref" => "B2234UK2026",
            "managing_agent" => "Lime Street Managing Agency Ltd",
            "coverholder" => "North Dock Coverholder Ltd"
          },
          "event_trail" => [
            {
              "event_type" => "underwriting_action_emitted",
              "payload" => {
                "action" => "ai_underwriting_action",
                "decision" => "manual_referral_required",
                "exposure_unit_id" => "uk-cyber-eu-2234",
                "policy_ref" => "B2234UK2026"
              }
            },
            {
              "event_type" => "control_check_recorded",
              "payload" => {
                "control_id" => "ctl-human-referral-calibration",
                "control_name" => "Quarterly human referral calibration",
                "status" => "pass",
                "control_type" => "risk_control",
                "evidence_ref" => "ev-human-referral-calibration-q3-2026"
              }
            },
            {
              "event_type" => "override_recorded",
              "payload" => {
                "override_id" => "ovr-review-2234",
                "override_type" => "manual_referral",
                "reason" => "Human review required because loss-history signal breached the referral floor.",
                "overridden_by" => "syndicate.underwriter@mand8.example",
                "effective_date" => "2026-07-17",
                "outcome" => "manual_referral_required"
              }
            }
          ],
          "human_review" => {
            "reviewer" => "syndicate.underwriter@mand8.example",
            "notes" => "Binding paused pending manual market review.",
            "status" => "reviewed",
            "reviewed_at" => "2026-07-17T10:05:00Z"
          }
        },
        "authority_receipts" => [
          {
            "case_id" => "case_mand8_lloyds_review_002",
            "receipt_id" => "arcpt_review_002",
            "action_id" => "act_authority_review_002",
            "issued_at" => "2026-07-17T10:01:00Z",
            "policy_ref" => "B2234UK2026",
            "binder_ref" => "B2234UK2026",
            "authority_id" => "auth-lma-binder-2234",
            "managing_agent" => "Lime Street Managing Agency Ltd",
            "coverholder" => "North Dock Coverholder Ltd",
            "controls_required" => ["Quarterly human referral calibration"],
            "human_review" => {
              "reviewer" => "managing.agent@mand8.example",
              "notes" => "Borderline confidence score requires underwriter review before binding.",
              "status" => "reviewed",
              "reviewed_at" => "2026-07-17T10:02:00Z"
            }
          }
        ],
        "incident_receipts" => [],
        "verification_reports" => [
          { "status" => "warning", "report_json" => { "status" => "warning", "details" => "manual_review" } }
        ],
        "review_request" => {
          "title" => "Manual referral review",
          "reviewer" => {
            "email" => "manual.review@mand8.example",
            "name" => "Manual Review Underwriter",
            "role" => "lloyds_underwriter"
          }
        }
      },
      "lloyds_incident_to_renewal" => {
        "workspace" => {
          "name" => "Lloyd's Incident To Renewal",
          "slug" => "mand8-lloyds-incident-renewal-edge"
        },
        "bundle_title" => "Renewal monitoring review bundle",
        "risk_receipt" => {
          "case_id" => "case_mand8_lloyds_incident_003",
          "receipt_id" => "rcpt_incident_003",
          "action_id" => "act_incident_003",
          "issued_at" => "2026-07-17T11:00:00Z",
          "decision" => "monitor_for_renewal",
          "domain_context" => {
            "exposure_unit_id" => "uk-cyber-eu-3234",
            "policy_ref" => "B3234UK2026",
            "risk_class" => "cyber",
            "insured_value" => 2_800_000.0,
            "currency" => "GBP",
            "territory" => "UK",
            "market_segment" => "lloyds_delegated_authority",
            "binder_ref" => "B3234UK2026",
            "managing_agent" => "Lime Street Managing Agency Ltd",
            "coverholder" => "North Dock Coverholder Ltd"
          },
          "event_trail" => [
            {
              "event_type" => "underwriting_action_emitted",
              "payload" => {
                "action" => "ai_underwriting_action",
                "decision" => "monitor_for_renewal",
                "exposure_unit_id" => "uk-cyber-eu-3234",
                "policy_ref" => "B3234UK2026"
              }
            },
            {
              "event_type" => "control_check_recorded",
              "payload" => {
                "control_id" => "ctl-monthly-anomaly-monitor",
                "control_name" => "Monthly anomaly monitoring",
                "status" => "pass",
                "control_type" => "risk_control",
                "evidence_ref" => "ev-monthly-anomaly-monitor-2026-07"
              }
            }
          ],
          "human_review" => {
            "reviewer" => "portfolio.actuary@mand8.example",
            "notes" => "Incident accepted into renewal monitoring pack.",
            "status" => "reviewed",
            "reviewed_at" => "2026-07-17T11:04:00Z"
          }
        },
        "authority_receipts" => [
          {
            "case_id" => "case_mand8_lloyds_incident_003",
            "receipt_id" => "arcpt_incident_003",
            "action_id" => "act_authority_incident_003",
            "issued_at" => "2026-07-17T11:01:00Z",
            "policy_ref" => "B3234UK2026",
            "binder_ref" => "B3234UK2026",
            "authority_id" => "auth-lma-binder-3234",
            "managing_agent" => "Lime Street Managing Agency Ltd",
            "coverholder" => "North Dock Coverholder Ltd",
            "controls_required" => ["Monthly anomaly monitoring"]
          }
        ],
        "incident_receipts" => [
          {
            "case_id" => "case_mand8_lloyds_incident_003",
            "incident_id" => "inc-3234-01",
            "incident_type" => "drift_alert",
            "severity" => "medium",
            "description" => "Model drift alert triggered during post-bind monitoring.",
            "claims_impact" => "monitor_for_renewal",
            "resolution" => {
              "outcome" => "monitoring_intensified",
              "next_review_at" => "2026-08-01"
            }
          }
        ],
        "verification_reports" => [
          { "status" => "passed", "report_json" => { "status" => "passed", "details" => "incident_bundle" } },
          { "status" => "warning", "report_json" => { "status" => "warning", "details" => "monitoring_follow_up" } }
        ],
        "review_request" => {
          "title" => "Renewal monitoring review",
          "reviewer" => {
            "email" => "carrier.innovation@mand8.example",
            "name" => "Carrier Innovation Reviewer",
            "role" => "carrier_innovation_team"
          }
        }
      }
    }.freeze

    ALIASES = {
      "lloyds_human_review_edge" => "lloyds_human_review_edge_case"
    }.freeze

    def self.available_scenarios
      SCENARIOS.keys.sort
    end

    def self.fetch(name)
      scenario = SCENARIOS[ALIASES.fetch(name, name)]
      raise ArgumentError, "Unknown MAND8 demo scenario: #{name}" unless scenario

      scenario.deep_dup
    end
  end
end
