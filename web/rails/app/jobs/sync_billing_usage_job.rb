class SyncBillingUsageJob < ApplicationJob
  queue_as :default

  def perform(billing_account_id)
    billing_account = BillingAccount.find(billing_account_id)
    result = Billing::ProviderFactory.for(billing_account.billing_provider).sync_usage!(billing_account: billing_account)
    AuditEvent.record!("billing.synced", auditable: billing_account, organization: billing_account.organization, request_id: "billing-sync-#{billing_account.id}", metadata: result)
  end
end
