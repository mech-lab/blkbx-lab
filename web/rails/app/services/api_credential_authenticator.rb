class ApiCredentialAuthenticator
  def self.call(token:)
    identifier, secret = token.to_s.split(".", 2)
    return if identifier.blank? || secret.blank?

    credential = ApiCredential.active.find_by(token_identifier: identifier)
    return unless credential&.usable? && credential.authenticate_secret(secret)

    credential.touch(:last_used_at)
    credential
  end
end
