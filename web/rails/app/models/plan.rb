class Plan < ApplicationRecord
  has_many :subscriptions, dependent: :destroy
  has_many :billing_accounts, through: :subscriptions

  # name: string - e.g., "ink_developer", "ink_assurance", "blkbxs_workspace"
  # product_type: string - "ink", "blkbxs", "mand8", "due", "enterprise"
  # price_cents: integer - price in cents
  # billing_interval: string - "monthly", "yearly"
  # features: jsonb - feature flags and limits
  # active: boolean - whether plan is available

  validates :name, presence: true, uniqueness: true
  validates :product_type, presence: true, inclusion: { in: %w[ink blkbxs mand8 due enterprise] }
  validates :price_cents, presence: true, numericality: { greater_than_or_equal_to: 0 }
  validates :billing_interval, presence: true, inclusion: { in: %w[monthly yearly] }

  scope :active, -> { where(active: true) }
  scope :for_product, ->(product) { where(product_type: product) }

  def self.seed_defaults
    [
      { name: "ink_developer", product_type: "ink", price_cents: 0, billing_interval: "monthly", features: { receipts: "usage", verification_volume: "basic", environments: 1 } },
      { name: "ink_assurance", product_type: "ink", price_cents: 49900, billing_interval: "monthly", features: { receipts: "high", verification_volume: "unlimited", environments: 3, key_rotation: true, audit_logs: true } },
      { name: "blkbxs_workspace", product_type: "blkbxs", price_cents: 99900, billing_interval: "monthly", features: { projects: 10, bank_reviews: 50, evidence_bundles: 100 } },
      { name: "mand8_workspace", product_type: "mand8", price_cents: 99900, billing_interval: "monthly", features: { systems_assessed: 10, underwriting_bundles: 50, renewals: 25 } },
      { name: "due_workspace", product_type: "due", price_cents: 99900, billing_interval: "monthly", features: { matters: 10, workflows: 50, evidence_bundles: 100 } },
      { name: "enterprise", product_type: "enterprise", price_cents: 0, billing_interval: "yearly", features: { private_deployment: true, custom_trust_roots: true, sso: true, retention_controls: true } }
    ].each do |attrs|
      find_or_create_by(name: attrs[:name]) do |plan|
        attrs.each { |key, value| plan.public_send("#{key}=", value) }
        plan.active = true
      end
    end
  end
end
