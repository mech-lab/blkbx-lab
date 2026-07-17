class BuildBundleJob < ApplicationJob
  queue_as :default

  def perform(workspace_id, bundle_type, receipt_ids, title, actor_id = nil, workflow_run_id = nil)
    workspace = Workspace.find(workspace_id)
    actor = actor_id.present? ? User.find_by(id: actor_id) : nil
    workflow_run = workflow_run_id.present? ? WorkflowRun.find_by(id: workflow_run_id) : nil
    receipts = workspace.receipts.where(id: receipt_ids)
    Ink::BuildBundle.call(
      organization: workspace.organization,
      workspace: workspace,
      bundle_type: bundle_type,
      title: title,
      receipts: receipts,
      actor: actor,
      workflow_run: workflow_run
    )
  end
end
