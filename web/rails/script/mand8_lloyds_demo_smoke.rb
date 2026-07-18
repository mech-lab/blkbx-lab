require "pathname"

scenario = ENV.fetch("MAND8_SMOKE_SCENARIO", "lloyds_cyber_happy_path")
output_dir = Pathname.new(
  ENV.fetch(
    "MAND8_SMOKE_OUTPUT_DIR",
    Rails.root.join("..", "..", "artifacts", "mand8-lloyds-demo-smoke").to_s
  )
)
output_dir.mkpath

SchemaCatalog.seed_defaults!
WorkflowCatalog.seed_defaults!

user = User.find_or_create_by!(email: "lloyds.demo@mand8.example") do |record|
  record.password = "password12345"
  record.password_confirmation = "password12345"
  record.confirmed_at = Time.current
end

organization = Organization.find_or_create_by!(slug: "lloyds-labs-demo") do |record|
  record.name = "Lloyd's Labs Demo"
end

Membership.find_or_create_by!(user: user, organization: organization) do |record|
  record.role = "owner"
end

workspace = organization.workspaces.find_or_create_by!(slug: "mand8-lloyds-labs-demo") do |record|
  record.name = "MAND8 Lloyd's Labs Demo"
  record.product_type = "mand8"
  record.active = true
  record.metadata = { "demo_scenario" => scenario }
end
workspace.update!(metadata: workspace.metadata.merge("demo_scenario" => scenario))

seed_result = Mand8::SeedDemoWorkspace.call(workspace: workspace, scenario: scenario, actor: user)
snapshot = Mand8::WorkspaceSnapshot.call(workspace)
case_summary = snapshot.fetch(:cases).find { |entry| entry["case_id"] == seed_result[:case_id] }
bundle = workspace.evidence_bundles.find(seed_result[:bundle_id])
bundle_handoff = bundle.manifest["verifier_handoff"]
workspace_handoff = snapshot.fetch(:verifier_handoff)

raise "Expected seeded MAND8 workspace verifier handoff to be unavailable" unless workspace_handoff["available"] == false
raise "Expected seeded MAND8 case verifier handoff to be unavailable" unless case_summary.dig("verifier_handoff", "available") == false
raise "Expected seeded MAND8 bundle verifier handoff to be unavailable" unless bundle_handoff["available"] == false

summary = {
  date: "2026-07-17",
  scenario: scenario,
  workspace_id: workspace.id,
  case_id: seed_result[:case_id],
  bundle_id: seed_result[:bundle_id],
  review_request_id: seed_result[:review_request_id],
  shared_bundle_id: seed_result[:shared_bundle_id],
  receipt_count: workspace.receipts.count,
  bundle_count: workspace.evidence_bundles.count,
  review_request_count: workspace.review_requests.count,
  case_summary: case_summary.slice(
    "case_id",
    "policy_ref",
    "binder_ref",
    "authority_status",
    "human_review_status",
    "incident_count",
    "renewal_ready",
    "review_request_statuses"
  ),
  workspace_verifier_handoff: workspace_handoff,
  case_verifier_handoff: case_summary.fetch("verifier_handoff"),
  bundle_verifier_handoff: bundle_handoff,
  expected_verifier_handoff_available: false,
  output_dir: output_dir.to_s
}

output_dir.join("dashboard.json").write(JSON.pretty_generate(snapshot))
output_dir.join("summary.json").write(JSON.pretty_generate(summary))

puts JSON.pretty_generate(
  {
    date: "2026-07-17",
    scenario: scenario,
    seed_result: seed_result,
    output_dir: output_dir.to_s,
    expected_verifier_handoff_available: false,
    case_verifier_handoff: case_summary.fetch("verifier_handoff")
  }
)
