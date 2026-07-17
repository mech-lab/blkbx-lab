class DashboardsController < AuthenticatedController
  def show
    authorize Current.workspace if Current.workspace

    payload = {
      brand: Current.brand,
      product: Current.product,
      organization: Current.organization&.as_json(only: %i[id name slug]),
      workspace: Current.workspace&.as_json(only: %i[id name slug product_type]),
      organizations: Current.user&.organizations&.order(:id)&.map { |organization| organization.as_json(only: %i[id name slug]) } || [],
      workspaces: Current.organization&.workspaces&.order(:id)&.map do |workspace|
        workspace.as_json(only: %i[id name slug product_type active]).merge(
          selected: workspace.id == Current.workspace&.id,
          select_path: "/api/v1/organizations/#{workspace.organization_id}/workspaces/#{workspace.id}/select"
        )
      end || [],
      counts: {
        receipts: Current.workspace&.receipts&.count.to_i,
        bundles: Current.workspace&.evidence_bundles&.count.to_i,
        verification_runs: Current.workspace&.verification_runs&.count.to_i,
        review_requests: Current.workspace&.review_requests&.count.to_i
      }
    }

    if Current.workspace&.product_type == "mand8"
      payload[:mand8] = Mand8::WorkspaceSnapshot.call(Current.workspace)
    end

    render json: payload
  end
end
