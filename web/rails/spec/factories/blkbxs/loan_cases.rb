FactoryBot.define do
  factory :blkbxs_loan_case, class: "Blkbxs::LoanCase" do
    association :organization
    association :workspace
    sprint_engagement { association(:blkbxs_sprint_engagement, organization: organization, workspace: workspace) }
    sequence(:case_number) { |n| "BLKBXS-SMB-250K-#{n.to_s.rjust(3, '0')}" }
    status { "draft" }
    scenario_type { "smb_250k_conditional_approval" }
    borrower_name { "Sample Main Street Business LLC" }
    bank_reviewer_name { "Design Partner Bank Reviewer" }
    requested_amount { 250_000 }
    metadata { {} }
  end
end
