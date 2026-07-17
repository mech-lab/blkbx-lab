Rails.application.config.filter_parameters += [
  :password,
  :password_confirmation,
  :token,
  :secret,
  :secret_hash,
  :registry_json,
  :policy_json,
  :metadata,
  :details
]
