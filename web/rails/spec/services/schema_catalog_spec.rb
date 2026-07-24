require "rails_helper"

RSpec.describe SchemaCatalog do
  it "seeds BLKBXS UBR schema definitions from the shared Python fixture package" do
    described_class.seed_defaults!

    receipt_schema = SchemaDefinition.find_by!(schema_key: "blkbxs.ubr.receipt.v1", schema_version: "1.0.0", organization_id: nil)
    bundle_schema = SchemaDefinition.find_by!(schema_key: "blkbxs.ubr.bundle.v1", schema_version: "1.0.0", organization_id: nil)
    report_schema = SchemaDefinition.find_by!(schema_key: "blkbxs.ubr.verifier_report.v1", schema_version: "1.0.0", organization_id: nil)

    expect(receipt_schema.domain).to eq("blkbxs")
    expect(receipt_schema.schema_json.fetch("title")).to eq("BLKBXS Universal Banking Receipt")
    expect(bundle_schema.domain).to eq("blkbxs")
    expect(report_schema.domain).to eq("blkbxs")
  end
end
