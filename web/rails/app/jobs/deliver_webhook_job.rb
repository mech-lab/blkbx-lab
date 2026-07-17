class DeliverWebhookJob < ApplicationJob
  queue_as :default

  def perform(webhook_endpoint_id, payload)
    endpoint = WebhookEndpoint.find(webhook_endpoint_id)
    endpoint.touch(:last_used_at)
    AuditEvent.record!(
      "webhook.delivered",
      auditable: endpoint,
      organization: endpoint.organization,
      workspace: endpoint.workspace,
      request_id: Current.request_id,
      metadata: { payload: payload }
    )
  end
end
