FactoryBot.define do
  factory :verification_policy do
    association :organization
    association :workspace
    name { "Default policy" }
    active { true }
    policy_json { { "schema" => "ink.verify-policy.v1" } }
    trust_anchors { [] }
    allowed_issuers { [] }
    required_claims { [] }
  end
end
