class InvoiceReference < ApplicationRecord
  belongs_to :organization
  belongs_to :billing_account

  validates :organization, :billing_account, :provider_invoice_id, :status, :amount_cents, :currency, presence: true

  scope :for_organization, ->(org) { where(organization: org) }
end
