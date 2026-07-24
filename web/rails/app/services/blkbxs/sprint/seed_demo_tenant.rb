module Blkbxs
  module Sprint
    class SeedDemoTenant
      def self.call
        user = User.find_or_initialize_by(email: "designpartner@blkbxs.example")
        user.name = "Design Partner Bank User"
        user.password = "password12345" if user.new_record?
        user.password_confirmation = "password12345" if user.new_record?
        user.confirmed_at ||= Time.current
        user.save!

        organization = Organization.find_or_create_by!(slug: "design-partner-bank") do |record|
          record.name = "Design Partner Bank"
        end
        Membership.find_or_create_by!(user: user, organization: organization) do |membership|
          membership.role = "owner"
        end

        workspace = organization.workspaces.find_or_create_by!(slug: "blkbxs-sprint-console") do |record|
          record.name = "BLKBXS Sprint Console"
          record.product_type = "blkbxs"
          record.active = true
          record.metadata = { "demo_scenario" => DemoCatalog::CANONICAL_EXTERNAL_SCENARIO }
        end
        workspace.update!(
          product_type: "blkbxs",
          metadata: workspace.metadata.merge(
            "demo_scenario" => DemoCatalog::CANONICAL_EXTERNAL_SCENARIO,
            "seed_events_requires_hosted_issuer" => true
          )
        )

        SeedSmb250kCase.call(
          organization: organization,
          workspace: workspace,
          actor: user,
          issue_events: false
        )
      end
    end
  end
end
