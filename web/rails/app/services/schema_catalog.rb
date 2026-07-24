class SchemaCatalog
  ROOT = Rails.root.join("..", "..").expand_path.freeze

  DEFAULTS = [
    { domain: "ink", key: "ink.receipt.v2", version: "2.0.0", path: ROOT.join("schemas", "ink.receipt.v2.schema.json") },
    { domain: "ink", key: "ink.verify-policy.v1", version: "1.0.0", path: ROOT.join("schemas", "ink.verify-policy.v1.schema.json") },
    { domain: "ink", key: "ink.verification-report.v1", version: "1.0.0", path: ROOT.join("schemas", "ink.verification-report.v1.schema.json") },
    { domain: "blkbxs", key: "blkbxs.ubr.receipt.v1", version: "1.0.0", path: ROOT.join("python", "blkbx_lab", "products", "blkbxs", "schemas", "blkbxs.ubr.receipt.v1.schema.json") },
    { domain: "blkbxs", key: "blkbxs.ubr.bundle.v1", version: "1.0.0", path: ROOT.join("python", "blkbx_lab", "products", "blkbxs", "schemas", "blkbxs.ubr.bundle.v1.schema.json") },
    { domain: "blkbxs", key: "blkbxs.ubr.verifier_report.v1", version: "1.0.0", path: ROOT.join("python", "blkbx_lab", "products", "blkbxs", "schemas", "blkbxs.ubr.verifier_report.v1.schema.json") },
    { domain: "mand8", key: "mand8.risk_receipt.v1", version: "1.0.0", path: ROOT.join("products", "mand8-sdk", "schemas", "mand8.risk_receipt.v1.schema.json") },
    { domain: "mand8", key: "mand8.authority_receipt.v1", version: "1.0.0", path: ROOT.join("products", "mand8-sdk", "schemas", "mand8.authority_receipt.v1.schema.json") },
    { domain: "mand8", key: "mand8.control_receipt.v1", version: "1.0.0", path: ROOT.join("products", "mand8-sdk", "schemas", "mand8.control_receipt.v1.schema.json") },
    { domain: "mand8", key: "mand8.incident_receipt.v1", version: "1.0.0", path: ROOT.join("products", "mand8-sdk", "schemas", "mand8.incident_receipt.v1.schema.json") },
    { domain: "mand8", key: "mand8.bundle.v1", version: "1.0.0", path: ROOT.join("products", "mand8-sdk", "schemas", "mand8.bundle.v1.schema.json") },
    { domain: "due", key: "due.legal_action_receipt.v1", version: "1.0.0", path: ROOT.join("products", "due-sdk", "schemas", "due.legal_action_receipt.v1.schema.json") },
    { domain: "due", key: "due.authority_receipt.v1", version: "1.0.0", path: ROOT.join("products", "due-sdk", "schemas", "due.authority_receipt.v1.schema.json") },
    { domain: "due", key: "due.privilege_receipt.v1", version: "1.0.0", path: ROOT.join("products", "due-sdk", "schemas", "due.privilege_receipt.v1.schema.json") },
    { domain: "due", key: "due.disclosure_receipt.v1", version: "1.0.0", path: ROOT.join("products", "due-sdk", "schemas", "due.disclosure_receipt.v1.schema.json") },
    { domain: "due", key: "due.dispute_bundle.v1", version: "1.0.0", path: ROOT.join("products", "due-sdk", "schemas", "due.dispute_bundle.v1.schema.json") }
  ].freeze

  def self.seed_defaults!
    DEFAULTS.each do |definition|
      next unless File.exist?(definition[:path])

      SchemaDefinition.find_or_initialize_by(
        schema_key: definition[:key],
        schema_version: definition[:version],
        organization_id: nil
      ).tap do |record|
        record.domain = definition[:domain]
        record.schema_json = JSON.parse(File.read(definition[:path]))
        record.source_path = definition[:path].to_s
        record.active = true
        record.save!
      end
    end
  end
end
