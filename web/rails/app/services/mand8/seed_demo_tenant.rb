module Mand8
  class SeedDemoTenant
    def self.call
      user = User.find_or_initialize_by(email: "lloydslabs@mand8.example")
      user.name = "Lloyd's Labs Demo User"
      user.password = "password12345" if user.new_record?
      user.password_confirmation = "password12345" if user.new_record?
      user.confirmed_at ||= Time.current
      user.save!

      organization = Organization.find_or_create_by!(slug: "lloyds-labs-demo") do |record|
        record.name = "Lloyd's Labs Demo"
      end
      Membership.find_or_create_by!(user: user, organization: organization) do |membership|
        membership.role = "owner"
      end

      DemoCatalog.available_scenarios.each do |scenario|
        definition = DemoCatalog.fetch(scenario)
        workspace = organization.workspaces.find_or_create_by!(slug: definition.dig("workspace", "slug")) do |record|
          record.name = definition.dig("workspace", "name")
          record.product_type = "mand8"
          record.active = true
          record.metadata = { "demo_scenario" => scenario }
        end
        workspace.update!(product_type: "mand8", metadata: workspace.metadata.merge("demo_scenario" => scenario))
        SeedDemoWorkspace.call(workspace: workspace, scenario: scenario, actor: user)
      end
    end
  end
end
