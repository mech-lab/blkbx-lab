class CreateBlkbxsSprintConsole < ActiveRecord::Migration[7.1]
  def change
    create_table :blkbxs_sprint_engagements do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.string :name, null: false
      t.string :status, null: false, default: "active"
      t.date :starts_on
      t.date :ends_on
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end
    add_index :blkbxs_sprint_engagements, %i[workspace_id name], unique: true
    add_index :blkbxs_sprint_engagements, %i[organization_id status]

    create_table :blkbxs_loan_cases do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :sprint_engagement, null: false, foreign_key: { to_table: :blkbxs_sprint_engagements }
      t.string :case_number, null: false
      t.string :status, null: false, default: "draft"
      t.string :scenario_type, null: false, default: "smb_250k_conditional_approval"
      t.string :borrower_name
      t.string :bank_reviewer_name
      t.decimal :requested_amount, precision: 12, scale: 2, default: 250000
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end
    add_index :blkbxs_loan_cases, %i[workspace_id case_number], unique: true
    add_index :blkbxs_loan_cases, %i[workspace_id scenario_type status]

    create_table :blkbxs_evidence_events do |t|
      t.references :loan_case, null: false, foreign_key: { to_table: :blkbxs_loan_cases }
      t.references :receipt, null: true, foreign_key: true
      t.string :external_id, null: false
      t.string :event_type, null: false
      t.string :actor_type, null: false
      t.string :actor_identifier
      t.string :source_system
      t.jsonb :payload, null: false, default: {}
      t.string :canonical_hash
      t.string :previous_event_hash
      t.integer :event_order, null: false, default: 0
      t.datetime :occurred_at, null: false
      t.timestamps
    end
    add_index :blkbxs_evidence_events, %i[loan_case_id external_id], unique: true
    add_index :blkbxs_evidence_events, %i[loan_case_id event_order]
    add_index :blkbxs_evidence_events, :receipt_id, unique: true, where: "receipt_id IS NOT NULL"

    create_table :blkbxs_reviewer_objections do |t|
      t.references :loan_case, null: false, foreign_key: { to_table: :blkbxs_loan_cases }
      t.string :function, null: false
      t.string :severity, null: false, default: "medium"
      t.string :status, null: false, default: "open"
      t.text :objection, null: false
      t.text :response
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end
    add_index :blkbxs_reviewer_objections, %i[loan_case_id function status], name: "index_blkbxs_objections_on_case_function_status"

    create_table :blkbxs_export_packages do |t|
      t.references :loan_case, null: false, foreign_key: { to_table: :blkbxs_loan_cases }
      t.references :evidence_bundle, null: true, foreign_key: true
      t.string :package_type, null: false, default: "final_bankability_packet"
      t.string :status, null: false, default: "pending"
      t.string :file_path
      t.string :storage_key
      t.string :sha256
      t.jsonb :manifest, null: false, default: {}
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end
    add_index :blkbxs_export_packages, %i[loan_case_id package_type created_at], name: "index_blkbxs_exports_on_case_type_created"
  end
end
