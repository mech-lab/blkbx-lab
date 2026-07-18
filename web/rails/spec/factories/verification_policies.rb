FactoryBot.define do
  factory :verification_policy do
    association :organization
    association :workspace
    name { "Default policy" }
    active { true }
    policy_json do
      {
        "schema" => "ink.verify-policy.v1",
        "policy_id" => "TEST_POLICY",
        "require_canonical_tlv_v2" => true,
        "allow_verify_only_formats" => false,
        "require_trusted_issuer" => false,
        "require_revocation_check" => false,
        "require_manifest_hash_match_when_manifest_present" => true,
        "require_evidence_summary_match_when_manifest_present" => true,
        "require_controls_summary_match_when_controls_present" => true,
        "allow_network" => false
      }
    end
    trust_anchors { [] }
    allowed_issuers { [] }
    required_claims { [] }
  end
end
