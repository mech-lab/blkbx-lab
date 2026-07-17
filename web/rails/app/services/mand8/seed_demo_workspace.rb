module Mand8
  class SeedDemoWorkspace
    def self.call(workspace:, scenario:, actor: nil)
      new(workspace: workspace, scenario: scenario, actor: actor).call
    end

    def initialize(workspace:, scenario:, actor:)
      @workspace = workspace
      @scenario = scenario
      @actor = actor
      @organization = workspace.organization
    end

    def call
      raise ArgumentError, "MAND8 demo seeding requires a MAND8 workspace" unless @workspace.product_type == "mand8"

      definition = DemoCatalog.fetch(@scenario)
      risk_receipt = upsert_insurability_receipt(definition.fetch("risk_receipt"))
      authority_receipts = Array(definition["authority_receipts"]).map.with_index do |body, index|
        upsert_authority_receipt(body, index)
      end
      incident_receipts = Array(definition["incident_receipts"]).map.with_index do |body, index|
        upsert_incident_receipt(body, index)
      end
      verification_policy = upsert_verification_policy
      Array(definition["verification_reports"]).each do |report|
        upsert_verification_run(risk_receipt, verification_policy, report)
      end
      bundle = upsert_bundle(definition, [risk_receipt, *authority_receipts, *incident_receipts])
      review_request, shared_bundle = upsert_review_request(definition, bundle)

      metadata = @workspace.metadata.merge(
        "demo_scenario" => @scenario,
        "seeded_case_id" => definition.dig("risk_receipt", "case_id"),
        "seeded_at" => Time.current.utc.iso8601
      )
      @workspace.update!(metadata: metadata)

      {
        scenario: @scenario,
        case_id: definition.dig("risk_receipt", "case_id"),
        receipt_ids: [risk_receipt, *authority_receipts, *incident_receipts].map(&:id),
        bundle_id: bundle.id,
        review_request_id: review_request.id,
        shared_bundle_id: shared_bundle.id
      }
    end

    private

    def upsert_insurability_receipt(body)
      normalized = ReceiptContract.insurability(body: body, domain_metadata: { case_id: body["case_id"] })
      upsert_receipt(
        workflow_kind: "insurability",
        schema_key: "mand8.risk_receipt.v1",
        external_id: "#{@scenario}:insurability",
        body: normalized,
        domain_metadata: {
          case_id: normalized["case_id"],
          policy_ref: normalized.dig("domain_context", "policy_ref"),
          binder_ref: normalized.dig("domain_context", "binder_ref")
        }
      )
    end

    def upsert_authority_receipt(body, index)
      normalized = ReceiptContract.authority(body: body, domain_metadata: { case_id: body["case_id"] })
      upsert_receipt(
        workflow_kind: "authority",
        schema_key: "mand8.authority_receipt.v1",
        external_id: "#{@scenario}:authority:#{index}",
        body: normalized,
        domain_metadata: {
          case_id: normalized["case_id"],
          policy_ref: normalized.dig("domain_context", "policy_ref"),
          binder_ref: normalized.dig("domain_context", "binder_ref")
        }
      )
    end

    def upsert_incident_receipt(body, index)
      normalized = ReceiptContract.incident(body: body, domain_metadata: { case_id: body["case_id"] })
      upsert_receipt(
        workflow_kind: "incident",
        schema_key: "mand8.incident_receipt.v1",
        external_id: "#{@scenario}:incident:#{index}",
        body: normalized,
        domain_metadata: {
          case_id: normalized["case_id"],
          incident_id: normalized["incident_id"]
        }
      )
    end

    def upsert_receipt(workflow_kind:, schema_key:, external_id:, body:, domain_metadata:)
      schema_definition = SchemaDefinition.find_by(schema_key: schema_key, schema_version: "1.0.0", organization_id: nil)
      receipt = @workspace.receipts.find_or_initialize_by(organization: @organization, external_id: external_id)
      receipt.assign_attributes(
        schema_definition: schema_definition,
        schema_key: schema_key,
        schema_version: "1.0.0",
        workflow_kind: workflow_kind,
        body_json: body,
        domain_metadata: domain_metadata,
        issued_at: body["issued_at"],
        storage_key: StorageKeyBuilder.call(kind: :receipt, organization_id: @organization.id, record_id: receipt.id || "pending", filename: "receipt.ink"),
        sha256: Digest::SHA256.hexdigest(JSON.generate(body))
      )
      receipt.workspace = @workspace
      receipt.organization = @organization
      receipt.save!
      receipt.update!(storage_key: StorageKeyBuilder.call(kind: :receipt, organization_id: @organization.id, record_id: receipt.id, filename: "receipt.ink"))
      receipt
    end

    def upsert_verification_policy
      @workspace.verification_policies.find_or_create_by!(organization: @organization, name: "MAND8 Demo Verification Policy") do |policy|
        policy.policy_json = {
          "schema" => "ink.verify-policy.v1",
          "name" => "MAND8 demo strict policy",
          "require_trusted_issuer" => false,
          "network_required" => false
        }
        policy.active = true
      end
    end

    def upsert_verification_run(receipt, verification_policy, report)
      run = @workspace.verification_runs.find_or_initialize_by(
        organization: @organization,
        receipt: receipt,
        verification_policy: verification_policy
      )
      run.assign_attributes(
        evidence_bundle: nil,
        status: report.fetch("status"),
        report_json: report.fetch("report_json"),
        verified_at: Time.current
      )
      run.save!
      run
    end

    def upsert_bundle(definition, receipts)
      title = definition.fetch("bundle_title")
      bundle = @workspace.evidence_bundles.find_by(title: title, bundle_type: "mand8_renewal")
      return bundle if bundle

      BuildRenewalBundle.call(
        organization: @organization,
        workspace: @workspace,
        actor: @actor,
        receipts: receipts,
        title: title
      )
    end

    def upsert_review_request(definition, bundle)
      existing = @workspace.review_requests.find_by(title: definition.dig("review_request", "title"), evidence_bundle: bundle)
      if existing
        return [existing, existing.shared_bundles.first || bundle.shared_bundles.first]
      end

      review_request, shared_bundle = Workflows::CreateReviewRequest.call(
        organization: @organization,
        workspace: @workspace,
        evidence_bundle: bundle,
        title: definition.dig("review_request", "title"),
        reviewer_email: definition.dig("review_request", "reviewer", "email"),
        reviewer_name: definition.dig("review_request", "reviewer", "name"),
        reviewer_role: definition.dig("review_request", "reviewer", "role"),
        actor: @actor
      )
      if shared_bundle.portal_accesses.empty?
        IssuePortalAccessJob.perform_now(shared_bundle.id, review_request.reviewer_id, @actor&.id)
      end
      [review_request, shared_bundle]
    end
  end
end
