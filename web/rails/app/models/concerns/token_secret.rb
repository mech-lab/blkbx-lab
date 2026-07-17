module TokenSecret
  extend ActiveSupport::Concern

  def issue_secret!(prefix:)
    identifier = "#{prefix}_#{SecureRandom.hex(6)}"
    secret = SecureRandom.hex(24)
    self.token_identifier = identifier
    self.secret_hash = BCrypt::Password.create(secret)
    "#{identifier}.#{secret}"
  end

  def authenticate_secret(secret)
    return false if secret_hash.blank? || secret.blank?

    BCrypt::Password.new(secret_hash).is_password?(secret)
  rescue BCrypt::Errors::InvalidHash
    false
  end

  def serializable_hash(options = nil)
    defaults = { except: %i[secret_hash] }
    super(defaults.merge(options || {}))
  end
end
