require "base64"

FactoryBot.define do
  factory :signing_key do
    association :organization
    association :workspace
    sequence(:key_identifier) { |n| "key-#{n}" }
    public_key { Base64.urlsafe_encode64("\x01" * 32, padding: false) }
    key_type { "Ed25519" }
    state { "pre_active" }
    usage { "receipt_signing" }
    custody_kind { "cloud_kms_hsm" }
    metadata { {} }
  end
end
