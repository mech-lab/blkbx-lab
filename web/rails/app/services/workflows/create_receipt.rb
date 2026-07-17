module Workflows
  class CreateReceipt
    def self.call(options = {})
      new(options).call
    end

    def initialize(options = {})
      @organization = options.fetch(:organization)
      @workspace = options.fetch(:workspace)
      @workflow_kind = options.fetch(:workflow_kind)
      @schema_key = options.fetch(:schema_key)
      @schema_version = options.fetch(:schema_version)
      @actor = options[:actor]
      @issuer = options[:issuer]
      @body = options.fetch(:body, {})
      @domain_metadata = options.fetch(:domain_metadata, {})
      @external_id = options[:external_id]
      @title = options[:title] || "#{@workspace.product_type} #{@workflow_kind.humanize}"
    end

    def call
      schema_definition = SchemaDefinition.find_by(schema_key: @schema_key, schema_version: @schema_version, organization_id: nil)
      workflow_definition = WorkflowDefinition.find_or_create_by!(
        organization: nil,
        workspace: nil,
        product_type: @workspace.product_type,
        workflow_kind: @workflow_kind
      ) do |definition|
        definition.name = @title
        definition.schema_keys = [@schema_key]
        definition.configuration = {}
        definition.active = true
      end

      workflow_run = WorkflowRun.create!(
        organization: @organization,
        workspace: @workspace,
        workflow_definition: workflow_definition,
        title: @title,
        status: "collecting",
        started_at: Time.current,
        subject_metadata: @domain_metadata,
        metadata: { schema_key: @schema_key }
      )

      receipt = Receipt.create!(
        organization: @organization,
        workspace: @workspace,
        issuer: @issuer,
        schema_definition: schema_definition,
        external_id: @external_id,
        schema_key: @schema_key,
        schema_version: @schema_version,
        workflow_kind: @workflow_kind,
        body_json: @body,
        domain_metadata: @domain_metadata,
        issued_at: Time.current
      )

      receipt.update!(
        storage_key: StorageKeyBuilder.call(kind: :receipt, organization_id: @organization.id, record_id: receipt.id, filename: "receipt.ink"),
        sha256: Digest::SHA256.hexdigest(JSON.generate(@body))
      )

      UsageEvent.track(
        "receipt.created",
        organization: @organization,
        workspace: @workspace,
        metadata: { receipt_id: receipt.id, workflow_kind: @workflow_kind }
      )
      AuditEvent.record!(
        "receipt.created",
        auditable: receipt,
        organization: @organization,
        workspace: @workspace,
        user: @actor,
        request_id: Current.request_id,
        resulting_state: receipt.attributes
      )

      [workflow_run, receipt]
    end
  end
end
