module Due
  class BuildDefensibilityBundle
    def self.call(organization:, workspace:, actor: nil, receipts:, title: "Legal defensibility bundle", workflow_run: nil)
      Ink::BuildBundle.call(
        organization: organization,
        workspace: workspace,
        actor: actor,
        receipts: receipts,
        title: title,
        workflow_run: workflow_run,
        bundle_type: "due_defensibility"
      )
    end
  end
end
