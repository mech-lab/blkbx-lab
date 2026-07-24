class AddProductionSigningManagement < ActiveRecord::Migration[7.1]
  def change
    change_table :receipts, bulk: true do |t|
      t.jsonb :portable_receipt_json, null: false, default: {}
      t.string :signing_key_identifier
      t.string :trust_registry_version
      t.string :revocation_version
      t.string :signer_request_id
    end

    change_table :signing_keys, bulk: true do |t|
      t.string :usage, null: false, default: "receipt_signing"
      t.string :custody_kind, null: false, default: "cloud_kms_hsm"
      t.string :external_reference
      t.datetime :activated_at
      t.datetime :retired_at
    end

    create_table :key_ceremonies do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :signing_key, null: true, foreign_key: true
      t.references :requested_by, null: true, foreign_key: { to_table: :users }
      t.string :ceremony_kind, null: false
      t.string :state, null: false, default: "pending_approval"
      t.datetime :scheduled_for
      t.datetime :executed_at
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end

    create_table :key_ceremony_approvals do |t|
      t.references :key_ceremony, null: false, foreign_key: true
      t.references :user, null: false, foreign_key: true
      t.string :approver_role, null: false
      t.string :state, null: false, default: "approved"
      t.text :note
      t.datetime :approved_at, null: false
      t.timestamps
    end
    add_index :key_ceremony_approvals, %i[key_ceremony_id user_id], unique: true, name: "index_key_ceremony_approvals_uniqueness"

    create_table :trust_publications do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :key_ceremony, null: true, foreign_key: true
      t.references :signing_key, null: true, foreign_key: true
      t.string :artifact_kind, null: false
      t.string :version, null: false
      t.string :state, null: false, default: "published"
      t.string :artifact_url
      t.jsonb :artifact_json, null: false, default: {}
      t.datetime :published_at
      t.timestamps
    end
    add_index :trust_publications, %i[organization_id artifact_kind version], unique: true, name: "index_trust_publications_uniqueness"
  end
end
