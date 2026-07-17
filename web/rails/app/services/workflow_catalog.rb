class WorkflowCatalog
  def self.seed_defaults!
    ProductCatalog.workflow_templates.each do |template|
      WorkflowDefinition.find_or_initialize_by(
        organization_id: nil,
        workspace_id: nil,
        product_type: template[:product_type],
        workflow_kind: template[:workflow_kind]
      ).tap do |record|
        record.name = template[:name]
        record.schema_keys = template[:schema_keys]
        record.configuration = template[:configuration]
        record.active = true
        record.save!
      end
    end
  end
end
