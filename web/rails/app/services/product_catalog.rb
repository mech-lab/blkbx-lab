class ProductCatalog
  PRODUCT_HOST_PATTERNS = {
    ink: /inkreceipts/i,
    blkbxs: /blkbxs/i,
    mand8: /mand8/i,
    due: /due/i
  }.freeze

  PRODUCT_LABELS = {
    ink: "INK Receipts",
    blkbxs: "BLKBXS",
    mand8: "MAND8",
    due: "DUE"
  }.freeze

  SHARED_CAPABILITIES = %w[
    receipts:write
    receipts:read
    verifications:create
    bundles:create
    trust_registries:read
    keys:manage
  ].freeze

  def self.product_for_host(host)
    normalized = host.to_s.downcase
    PRODUCT_HOST_PATTERNS.each do |product, pattern|
      return product if normalized.match?(pattern)
    end
    :ink
  end

  def self.brand_for(product)
    PRODUCT_LABELS.fetch(product.to_sym, PRODUCT_LABELS[:ink])
  end

  def self.identity_host?(host)
    host.to_s.downcase.start_with?("accounts.")
  end

  def self.valid_target_host?(host)
    normalized = host.to_s.downcase
    PRODUCT_HOST_PATTERNS.values.any? { |pattern| normalized.match?(pattern) }
  end

  def self.workflow_templates
    [
      { product_type: "blkbxs", workflow_kind: "vendor_onboarding", name: "Vendor onboarding evidence", schema_keys: ["blkbxs.vendor_onboarding_receipt.v1"], configuration: { bundle_type: "blkbxs_bank_diligence" } },
      { product_type: "blkbxs", workflow_kind: "control_execution", name: "Bank control evidence", schema_keys: ["blkbxs.control_receipt.v1"], configuration: { bundle_type: "blkbxs_bank_diligence" } },
      { product_type: "blkbxs", workflow_kind: "underwriting_decision", name: "Underwriting decision evidence", schema_keys: ["blkbxs.underwriting_decision_receipt.v1"], configuration: { bundle_type: "blkbxs_bank_diligence" } },
      { product_type: "blkbxs", workflow_kind: "ubr_event", name: "Universal banking event evidence", schema_keys: ["blkbxs.ubr.receipt.v1"], configuration: { bundle_type: "blkbxs_ubr_graph" } },
      { product_type: "mand8", workflow_kind: "insurability", name: "Insurability evidence", schema_keys: ["mand8.risk_receipt.v1"], configuration: { bundle_type: "mand8_insurability" } },
      { product_type: "mand8", workflow_kind: "authority", name: "Authority and binder evidence", schema_keys: ["mand8.authority_receipt.v1"], configuration: { bundle_type: "mand8_renewal" } },
      { product_type: "mand8", workflow_kind: "incident", name: "Incident evidence", schema_keys: ["mand8.incident_receipt.v1"], configuration: { bundle_type: "mand8_renewal" } },
      { product_type: "due", workflow_kind: "reasoning", name: "Legal reasoning evidence", schema_keys: ["due.legal_action_receipt.v1"], configuration: { bundle_type: "due_defensibility" } },
      { product_type: "due", workflow_kind: "authority", name: "Authority evidence", schema_keys: ["due.authority_receipt.v1"], configuration: { bundle_type: "due_defensibility" } },
      { product_type: "due", workflow_kind: "privilege", name: "Privilege evidence", schema_keys: ["due.privilege_receipt.v1"], configuration: { bundle_type: "due_defensibility" } },
      { product_type: "due", workflow_kind: "disclosure", name: "Disclosure evidence", schema_keys: ["due.disclosure_receipt.v1"], configuration: { bundle_type: "due_defensibility" } }
    ].freeze
  end
end
