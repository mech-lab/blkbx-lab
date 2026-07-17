Rails.application.configure do
  config.cache_classes = true
  config.eager_load = true
  config.consider_all_requests_local = false
  config.public_file_server.enabled = ENV["RAILS_SERVE_STATIC_FILES"].present?
  config.force_ssl = ENV.fetch("FORCE_SSL", "1") == "1"
  config.log_level = ENV.fetch("RAILS_LOG_LEVEL", "info")
  config.active_storage.service = :s3
  config.action_mailer.default_url_options = { host: "accounts.inkreceipts.dev", protocol: "https" }
end
