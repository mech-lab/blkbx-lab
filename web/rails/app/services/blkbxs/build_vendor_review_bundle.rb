module Blkbxs
  class BuildVendorReviewBundle
    def self.call(organization:, workspace:, actor: nil, receipts:, title: "Bank diligence bundle", workflow_run: nil)
      Ink::BuildBundle.call(
        organization: organization,
        workspace: workspace,
        actor: actor,
        receipts: receipts,
        title: title,
        workflow_run: workflow_run,
        bundle_type: "blkbxs_bank_diligence"
      )
    end
  end
end
