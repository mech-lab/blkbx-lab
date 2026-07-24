FactoryBot.define do
  factory :blkbxs_sprint_engagement, class: "Blkbxs::SprintEngagement" do
    association :organization
    association :workspace
    name { "BLKBXS SMB $250k Evidence Sprint" }
    status { "active" }
    starts_on { Date.current }
    ends_on { 75.days.from_now.to_date }
    metadata { {} }
  end
end
