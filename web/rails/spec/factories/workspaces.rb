FactoryBot.define do
  factory :workspace do
    association :organization
    sequence(:name) { |n| "Workspace #{n}" }
    sequence(:slug) { |n| "workspace-#{n}" }
    product_type { "ink" }
    active { true }
    metadata { {} }
  end
end
