module Keys
  class ExecuteCeremony
    def self.call(ceremony:, action:)
      new(ceremony: ceremony, action: action).call
    end

    def initialize(ceremony:, action:)
      @ceremony = ceremony
      @action = action
    end

    def call
      raise ArgumentError, "approval quorum not satisfied" unless @ceremony.approval_quorum_met?
      raise ArgumentError, "signing key required" unless @ceremony.signing_key

      now = Time.current
      case @action
      when "activate"
        retire_existing_active_receipt_signers!(now) if @ceremony.signing_key.usage == "receipt_signing"
        @ceremony.signing_key.update!(state: "active", activated_at: now, retired_at: nil)
        @ceremony.update!(state: "activated", executed_at: now)
      when "retire"
        @ceremony.signing_key.update!(state: "retired", retired_at: now)
        @ceremony.update!(state: "retired", executed_at: now)
      when "revoke"
        @ceremony.signing_key.update!(state: "revoked", revoked_at: now)
        @ceremony.update!(state: "revoked", executed_at: now)
      else
        raise ArgumentError, "unsupported ceremony action #{@action}"
      end

      @ceremony
    end

    private

    def retire_existing_active_receipt_signers!(now)
      @ceremony.organization
               .signing_keys
               .receipt_signing
               .active
               .where.not(id: @ceremony.signing_key_id)
               .update_all(state: "retired", retired_at: now)
    end
  end
end
