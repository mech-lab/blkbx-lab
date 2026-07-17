Devise.setup do |config|
  config.mailer_sender = ENV.fetch("DEVISE_MAILER_SENDER", "no-reply@inkreceipts.dev")
  require "devise/orm/active_record"

  config.case_insensitive_keys = [:email]
  config.strip_whitespace_keys = [:email]
  config.skip_session_storage = [:http_auth]
  config.stretches = Rails.env.test? ? 1 : 12
  config.reconfirmable = true
  config.expire_all_remember_me_on_sign_out = true
  config.password_length = 12..128
  config.timeout_in = 30.minutes
  config.sign_out_via = :delete
  config.jwt do |jwt|
    jwt.secret = ENV.fetch("DEVISE_JWT_SECRET_KEY", "development-jwt-secret-change-me")
    jwt.dispatch_requests = []
    jwt.revocation_requests = []
  end
end
