FactoryBot.define do
  factory :organization do
    sequence(:name) { |n| "Organization #{n}" }
    sequence(:slug) { |n| "organization-#{n}" }
    metadata { {} }
  end
end
