FactoryBot.define do
  factory :membership do
    association :user
    association :organization
    role { "owner" }
  end
end
