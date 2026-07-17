module Identity
  class ConsumeSessionHandoff
    def self.call(options = {})
      new(options).call
    end

    def initialize(options = {})
      @token = options.fetch(:token).to_s
      @host = options.fetch(:host)
    end

    def call
      identifier, secret = @token.split(".", 2)
      handoff = SessionHandoff.active.find_by(token_identifier: identifier, target_host: @host)
      return unless handoff&.authenticate_secret(secret)

      handoff.update!(used_at: Time.current)
      handoff
    end
  end
end
