module Billing
  module Providers
    class StripeGateway
      def sync_usage!(billing_account:)
        {
          billing_account_id: billing_account.id,
          provider: billing_account.billing_provider,
          synced_at: Time.current
        }
      end
    end
  end
end
