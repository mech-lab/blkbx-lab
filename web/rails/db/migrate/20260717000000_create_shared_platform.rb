class CreateSharedPlatform < ActiveRecord::Migration[7.1]
  def change
    enable_extension "pgcrypto" unless extension_enabled?("pgcrypto")

    create_table :users do |t|
      t.string :name
      t.string :email, null: false, default: ""
      t.string :encrypted_password, null: false, default: ""
      t.string :reset_password_token
      t.datetime :reset_password_sent_at
      t.datetime :remember_created_at
      t.integer :sign_in_count, default: 0, null: false
      t.datetime :current_sign_in_at
      t.datetime :last_sign_in_at
      t.string :current_sign_in_ip
      t.string :last_sign_in_ip
      t.string :confirmation_token
      t.datetime :confirmed_at
      t.datetime :confirmation_sent_at
      t.string :unconfirmed_email
      t.timestamps
    end
    add_index :users, :email, unique: true
    add_index :users, :reset_password_token, unique: true
    add_index :users, :confirmation_token, unique: true

    create_table :organizations do |t|
      t.string :name, null: false
      t.string :slug, null: false
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end
    add_index :organizations, :slug, unique: true

    create_table :memberships do |t|
      t.references :user, null: false, foreign_key: true
      t.references :organization, null: false, foreign_key: true
      t.string :role, null: false
      t.timestamps
    end
    add_index :memberships, %i[user_id organization_id], unique: true

    create_table :workspaces do |t|
      t.references :organization, null: false, foreign_key: true
      t.string :name, null: false
      t.string :slug, null: false
      t.string :product_type, null: false
      t.boolean :active, null: false, default: true
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end
    add_index :workspaces, %i[organization_id slug], unique: true
    add_index :workspaces, %i[organization_id product_type]

    create_table :billing_accounts do |t|
      t.references :organization, null: false, foreign_key: true
      t.string :billing_provider, null: false, default: "stripe"
      t.string :provider_customer_id
      t.string :status, null: false, default: "active"
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end
    add_index :billing_accounts, :organization_id, unique: true

    create_table :plans do |t|
      t.string :name, null: false
      t.string :product_type, null: false
      t.integer :price_cents, null: false, default: 0
      t.string :billing_interval, null: false
      t.boolean :active, null: false, default: true
      t.jsonb :features, null: false, default: {}
      t.timestamps
    end
    add_index :plans, :name, unique: true

    create_table :subscriptions do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :billing_account, null: false, foreign_key: true
      t.references :plan, null: false, foreign_key: true
      t.string :status, null: false, default: "active"
      t.datetime :current_period_start
      t.datetime :current_period_end
      t.boolean :cancel_at_period_end, null: false, default: false
      t.string :provider_subscription_id
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end

    create_table :invoice_references do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :billing_account, null: false, foreign_key: true
      t.string :provider_invoice_id, null: false
      t.string :status, null: false
      t.integer :amount_cents, null: false, default: 0
      t.string :currency, null: false, default: "usd"
      t.datetime :period_start
      t.datetime :period_end
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end
    add_index :invoice_references, :provider_invoice_id, unique: true

    create_table :usage_events do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :billing_account, null: false, foreign_key: true
      t.references :workspace, null: true, foreign_key: true
      t.references :subscription, null: true, foreign_key: true
      t.string :event_type, null: false
      t.integer :quantity, null: false, default: 1
      t.jsonb :metadata, null: false, default: {}
      t.datetime :occurred_at, null: false
      t.timestamps
    end
    add_index :usage_events, %i[organization_id event_type occurred_at]

    create_table :applications do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.string :name, null: false
      t.string :slug, null: false
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end
    add_index :applications, %i[organization_id slug], unique: true

    create_table :environments do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :application, null: false, foreign_key: true
      t.string :name, null: false
      t.string :environment_type, null: false
      t.boolean :active, null: false, default: true
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end
    add_index :environments, %i[application_id name], unique: true

    create_table :api_credentials do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :environment, null: true, foreign_key: true
      t.string :name, null: false
      t.string :token_identifier, null: false
      t.string :secret_hash, null: false
      t.jsonb :capabilities, null: false, default: []
      t.boolean :active, null: false, default: true
      t.datetime :expires_at
      t.datetime :last_used_at
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end
    add_index :api_credentials, :token_identifier, unique: true
    add_index :api_credentials, %i[workspace_id active]

    create_table :webhook_endpoints do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :environment, null: true, foreign_key: true
      t.string :url, null: false
      t.string :token_identifier, null: false
      t.string :secret_hash, null: false
      t.boolean :active, null: false, default: true
      t.datetime :last_used_at
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end
    add_index :webhook_endpoints, :token_identifier, unique: true

    create_table :sdk_installations do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :application, null: true, foreign_key: true
      t.string :sdk_name, null: false
      t.string :sdk_version, null: false
      t.string :installation_kind, null: false
      t.datetime :last_seen_at
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end

    create_table :issuers do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.string :name, null: false
      t.string :slug, null: false
      t.text :public_key, null: false
      t.string :key_type, null: false
      t.boolean :active, null: false, default: true
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end
    add_index :issuers, %i[organization_id slug], unique: true

    create_table :signing_keys do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :issuer, null: true, foreign_key: true
      t.string :key_identifier, null: false
      t.text :public_key, null: false
      t.string :key_type, null: false
      t.string :state, null: false, default: "active"
      t.datetime :revoked_at
      t.datetime :expires_at
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end
    add_index :signing_keys, %i[organization_id key_identifier], unique: true

    create_table :trust_registries do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.string :name, null: false
      t.jsonb :registry_json, null: false, default: {}
      t.jsonb :trust_anchors, null: false, default: []
      t.boolean :active, null: false, default: true
      t.timestamps
    end

    create_table :schema_definitions do |t|
      t.references :organization, null: true, foreign_key: true
      t.string :schema_key, null: false
      t.string :schema_version, null: false
      t.string :domain, null: false
      t.jsonb :schema_json, null: false, default: {}
      t.string :source_path
      t.boolean :active, null: false, default: true
      t.timestamps
    end
    add_index :schema_definitions, %i[organization_id schema_key schema_version], unique: true, name: "index_schema_definitions_uniqueness"

    create_table :verification_policies do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :trust_registry, null: true, foreign_key: true
      t.references :schema_definition, null: true, foreign_key: true
      t.string :name, null: false
      t.boolean :active, null: false, default: true
      t.jsonb :policy_json, null: false, default: {}
      t.jsonb :trust_anchors, null: false, default: []
      t.jsonb :allowed_issuers, null: false, default: []
      t.jsonb :required_claims, null: false, default: []
      t.timestamps
    end

    create_table :workflow_definitions do |t|
      t.references :organization, null: true, foreign_key: true
      t.references :workspace, null: true, foreign_key: true
      t.string :product_type, null: false
      t.string :workflow_kind, null: false
      t.string :name, null: false
      t.jsonb :schema_keys, null: false, default: []
      t.jsonb :configuration, null: false, default: {}
      t.boolean :active, null: false, default: true
      t.timestamps
    end
    add_index :workflow_definitions, %i[organization_id workspace_id product_type workflow_kind], unique: true, name: "index_workflow_definitions_uniqueness"

    create_table :customer_organizations do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.string :name, null: false
      t.string :slug, null: false
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end
    add_index :customer_organizations, %i[organization_id slug], unique: true

    create_table :customer_projects do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :customer_organization, null: true, foreign_key: true
      t.string :name, null: false
      t.string :slug, null: false
      t.string :project_type, null: false
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end
    add_index :customer_projects, %i[organization_id slug], unique: true

    create_table :reviewers do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :customer_organization, null: true, foreign_key: true
      t.references :user, null: true, foreign_key: true
      t.string :email, null: false
      t.string :name, null: false
      t.string :role, null: false
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end
    add_index :reviewers, %i[organization_id email], unique: true

    create_table :receipts do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :issuer, null: true, foreign_key: true
      t.references :schema_definition, null: true, foreign_key: true
      t.string :external_id
      t.string :schema_key, null: false
      t.string :schema_version, null: false
      t.string :workflow_kind
      t.string :storage_key
      t.string :sha256
      t.jsonb :body_json, null: false, default: {}
      t.jsonb :domain_metadata, null: false, default: {}
      t.datetime :issued_at
      t.timestamps
    end
    add_index :receipts, %i[organization_id external_id], unique: true, where: "external_id IS NOT NULL"
    add_index :receipts, %i[workspace_id schema_key workflow_kind]

    create_table :payload_artifacts do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :receipt, null: false, foreign_key: true
      t.string :storage_key, null: false
      t.string :sha256, null: false
      t.bigint :byte_size, null: false
      t.string :content_type, null: false
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end
    add_index :payload_artifacts, :storage_key, unique: true

    create_table :evidence_artifacts do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :receipt, null: false, foreign_key: true
      t.string :artifact_kind
      t.string :storage_key, null: false
      t.string :sha256, null: false
      t.bigint :byte_size, null: false
      t.string :content_type, null: false
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end
    add_index :evidence_artifacts, :storage_key, unique: true

    create_table :workflow_runs do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :workflow_definition, null: false, foreign_key: true
      t.references :customer_project, null: true, foreign_key: true
      t.references :evidence_bundle, null: true
      t.string :title, null: false
      t.string :status, null: false, default: "draft"
      t.datetime :started_at
      t.datetime :completed_at
      t.jsonb :subject_metadata, null: false, default: {}
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end

    create_table :evidence_bundles do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :workflow_run, null: true
      t.references :created_by, null: true, foreign_key: { to_table: :users }
      t.string :bundle_type, null: false
      t.string :title
      t.string :status, null: false, default: "draft"
      t.string :storage_key
      t.string :sha256
      t.jsonb :manifest, null: false, default: {}
      t.timestamps
    end
    add_foreign_key :workflow_runs, :evidence_bundles, column: :evidence_bundle_id

    create_table :evidence_bundle_artifacts do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :evidence_bundle, null: false, foreign_key: true
      t.references :evidence_artifact, null: false, foreign_key: true
      t.integer :position
      t.timestamps
    end
    add_index :evidence_bundle_artifacts, %i[evidence_bundle_id evidence_artifact_id], unique: true, name: "index_bundle_artifacts_uniqueness"

    create_table :verification_runs do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :receipt, null: false, foreign_key: true
      t.references :evidence_bundle, null: true, foreign_key: true
      t.references :verification_policy, null: false, foreign_key: true
      t.string :status, null: false, default: "pending"
      t.jsonb :report_json, null: false, default: {}
      t.text :error_message
      t.datetime :verified_at
      t.timestamps
    end

    create_table :review_requests do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :evidence_bundle, null: false, foreign_key: true
      t.references :workflow_run, null: true, foreign_key: true
      t.references :customer_project, null: true, foreign_key: true
      t.references :reviewer, null: true, foreign_key: true
      t.string :title, null: false
      t.string :status, null: false, default: "pending"
      t.datetime :requested_at
      t.datetime :due_at
      t.text :decision_notes
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end

    create_table :shared_bundles do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :evidence_bundle, null: false, foreign_key: true
      t.references :review_request, null: true, foreign_key: true
      t.string :name, null: false
      t.string :status, null: false, default: "active"
      t.datetime :expires_at
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end

    create_table :portal_accesses do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :shared_bundle, null: false, foreign_key: true
      t.references :reviewer, null: true, foreign_key: true
      t.string :token_identifier, null: false
      t.string :secret_hash, null: false
      t.datetime :expires_at, null: false
      t.datetime :used_at
      t.datetime :last_accessed_at
      t.timestamps
    end
    add_index :portal_accesses, :token_identifier, unique: true

    create_table :download_events do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :shared_bundle, null: false, foreign_key: true
      t.references :portal_access, null: true, foreign_key: true
      t.references :reviewer, null: true, foreign_key: true
      t.string :artifact_type, null: false
      t.jsonb :metadata, null: false, default: {}
      t.datetime :downloaded_at, null: false
      t.timestamps
    end

    create_table :controls do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :workflow_definition, null: true, foreign_key: true
      t.string :name, null: false
      t.string :kind, null: false
      t.string :status
      t.jsonb :details, null: false, default: {}
      t.timestamps
    end

    create_table :control_executions do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :control, null: false, foreign_key: true
      t.references :workflow_run, null: true, foreign_key: true
      t.references :receipt, null: true, foreign_key: true
      t.string :status, null: false, default: "pending"
      t.jsonb :details, null: false, default: {}
      t.datetime :executed_at
      t.timestamps
    end

    create_table :claims do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :receipt, null: true, foreign_key: true
      t.references :workflow_run, null: true, foreign_key: true
      t.string :kind, null: false
      t.jsonb :body, null: false, default: {}
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end

    create_table :decisions do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :receipt, null: true, foreign_key: true
      t.references :workflow_run, null: true, foreign_key: true
      t.string :kind, null: false
      t.string :outcome, null: false
      t.jsonb :details, null: false, default: {}
      t.datetime :decided_at
      t.timestamps
    end

    create_table :approvals do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :review_request, null: true, foreign_key: true
      t.references :workflow_run, null: true, foreign_key: true
      t.references :user, null: true, foreign_key: true
      t.references :reviewer, null: true, foreign_key: true
      t.string :status, null: false
      t.text :notes
      t.datetime :decided_at
      t.jsonb :metadata, null: false, default: {}
      t.timestamps
    end

    create_table :workflow_exceptions do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :workflow_run, null: false, foreign_key: true
      t.references :receipt, null: true, foreign_key: true
      t.string :kind, null: false
      t.string :status, null: false, default: "open"
      t.jsonb :details, null: false, default: {}
      t.datetime :opened_at
      t.datetime :resolved_at
      t.timestamps
    end

    create_table :remediations do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: false, foreign_key: true
      t.references :workflow_exception, null: false, foreign_key: true
      t.references :workflow_run, null: true, foreign_key: true
      t.string :status, null: false, default: "open"
      t.jsonb :details, null: false, default: {}
      t.datetime :due_at
      t.datetime :resolved_at
      t.timestamps
    end

    create_table :audit_events do |t|
      t.references :organization, null: false, foreign_key: true
      t.references :workspace, null: true, foreign_key: true
      t.references :user, null: true, foreign_key: true
      t.references :api_credential, null: true, foreign_key: true
      t.string :event_type, null: false
      t.string :auditable_type
      t.bigint :auditable_id
      t.string :request_id
      t.jsonb :prior_state, null: false, default: {}
      t.jsonb :resulting_state, null: false, default: {}
      t.jsonb :metadata, null: false, default: {}
      t.datetime :occurred_at, null: false
      t.timestamps
    end
    add_index :audit_events, %i[auditable_type auditable_id]
    add_index :audit_events, %i[organization_id occurred_at]

    create_table :session_handoffs do |t|
      t.references :user, null: false, foreign_key: true
      t.references :organization, null: true, foreign_key: true
      t.references :workspace, null: true, foreign_key: true
      t.string :target_host, null: false
      t.string :token_identifier, null: false
      t.string :secret_hash, null: false
      t.datetime :expires_at, null: false
      t.datetime :used_at
      t.timestamps
    end
    add_index :session_handoffs, :token_identifier, unique: true
  end
end
