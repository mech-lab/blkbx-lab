class Workspace < ApplicationRecord
  belongs_to :organization
  has_many :applications, dependent: :destroy
  has_many :environments, dependent: :destroy
  has_many :api_credentials, dependent: :destroy
  has_many :webhook_endpoints, dependent: :destroy
  has_many :sdk_installations, dependent: :destroy
  has_many :issuers, dependent: :destroy
  has_many :signing_keys, dependent: :destroy
  has_many :key_ceremonies, dependent: :destroy
  has_many :trust_publications, dependent: :destroy
  has_many :trust_registries, dependent: :destroy
  has_many :receipts, dependent: :destroy
  has_many :payload_artifacts, dependent: :destroy
  has_many :evidence_artifacts, dependent: :destroy
  has_many :evidence_bundles, dependent: :destroy
  has_many :verification_policies, dependent: :destroy
  has_many :verification_runs, dependent: :destroy
  has_many :customer_organizations, dependent: :destroy
  has_many :workflow_runs, dependent: :destroy
  has_many :customer_projects, dependent: :destroy
  has_many :reviewers, dependent: :destroy
  has_many :review_requests, dependent: :destroy
  has_many :shared_bundles, dependent: :destroy
  has_many :portal_accesses, dependent: :destroy
  has_many :download_events, dependent: :destroy
  has_many :workflow_definitions, dependent: :destroy
  has_many :controls, dependent: :destroy
  has_many :control_executions, dependent: :destroy
  has_many :claims, dependent: :destroy
  has_many :decisions, dependent: :destroy
  has_many :approvals, dependent: :destroy
  has_many :workflow_exceptions, dependent: :destroy
  has_many :remediations, dependent: :destroy
  has_many :audit_events, dependent: :destroy
  has_many :usage_events, dependent: :destroy
  has_many :blkbxs_sprint_engagements, class_name: "Blkbxs::SprintEngagement", dependent: :destroy
  has_many :blkbxs_loan_cases, class_name: "Blkbxs::LoanCase", dependent: :destroy

  enum product_type: {
    ink: "ink",
    blkbxs: "blkbxs",
    mand8: "mand8",
    due: "due"
  }

  validates :name, :slug, presence: true
  validates :slug, uniqueness: { scope: :organization_id }
  validates :product_type, presence: true, inclusion: { in: product_types.keys }

  def current_product
    Current.product
  end

  def product_specific?
    product_type != "ink"
  end
end
