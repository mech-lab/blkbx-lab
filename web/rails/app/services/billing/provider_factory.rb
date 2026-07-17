module Billing
  class ProviderFactory
    def self.for(name)
      case name.to_s
      when "stripe"
        Billing::Providers::StripeGateway.new
      else
        Billing::Providers::StripeGateway.new
      end
    end
  end
end
