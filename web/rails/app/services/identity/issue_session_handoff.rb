module Identity
  class IssueSessionHandoff
    def self.call(options = {})
      new(options).call
    end

    def initialize(options = {})
      @user = options.fetch(:user)
      @target_host = options.fetch(:target_host)
      @organization = options[:organization]
      @workspace = options[:workspace]
    end

    def call
      raise ArgumentError, "invalid target host" unless ProductCatalog.valid_target_host?(@target_host)

      handoff = SessionHandoff.new(
        user: @user,
        organization: @organization,
        workspace: @workspace,
        target_host: @target_host,
        expires_at: 10.minutes.from_now
      )
      token = handoff.issue_secret!(prefix: "handoff")
      handoff.save!
      {
        token: token,
        consume_url: "https://#{@target_host}/accounts/session_handoffs/consume?token=#{CGI.escape(token)}"
      }
    end
  end
end
