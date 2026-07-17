class PortalAccessAuthenticator
  def self.call(token:, shared_bundle:)
    identifier, secret = token.to_s.split(".", 2)
    return if identifier.blank? || secret.blank?

    access = shared_bundle.portal_accesses.active.find_by(token_identifier: identifier)
    return unless access&.authenticate_secret(secret)

    access.touch(:last_accessed_at)
    access
  end
end
