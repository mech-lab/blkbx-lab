FactoryBot.define do
  factory :user do
    sequence(:email) { |n| "user#{n}@example.com" }
    password { "password12345" }
    password_confirmation { "password12345" }
    confirmed_at { Time.current }
  end
end
