module Due
  class ExportMatter
    def self.call(organization:, workspace:, actor: nil, customer_project:, receipts:)
      bundle = BuildDefensibilityBundle.call(
        organization: organization,
        workspace: workspace,
        actor: actor,
        receipts: receipts,
        title: "#{customer_project.name} defensibility export"
      )

      { customer_project: customer_project, evidence_bundle: bundle }
    end
  end
end
