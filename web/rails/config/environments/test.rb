Rails.application.configure do
  config.cache_classes = true
  config.eager_load = ENV["CI"].present?
  config.public_file_server.enabled = true
  config.public_file_server.headers = { "Cache-Control" => "public, max-age=3600" }
  config.consider_all_requests_local = true
  config.action_controller.perform_caching = false
  config.cache_store = :null_store
  config.action_dispatch.show_exceptions = false
  config.action_controller.allow_forgery_protection = false
  config.secret_key_base = ENV.fetch("SECRET_KEY_BASE", "test-secret-key-base-change-me")
  config.active_storage.service = :local
  config.action_mailer.delivery_method = :test
  config.action_mailer.default_url_options = { host: "accounts.inkreceipts.dev", protocol: "https" }
  config.active_support.deprecation = :stderr
  config.active_job.queue_adapter = :test
end
