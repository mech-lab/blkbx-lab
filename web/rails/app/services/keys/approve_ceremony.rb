require "digest"
require "json"

module Keys
  class ApproveCeremony
    def self.call(ceremony:, actor:, note: nil)
      new(ceremony: ceremony, actor: actor, note: note).call
    end

    def initialize(ceremony:, actor:, note:)
      @ceremony = ceremony
      @actor = actor
      @note = note
    end

    def call
      membership = @ceremony.organization.memberships.find_by!(user: @actor)
      approval = @ceremony.key_ceremony_approvals.find_or_initialize_by(user: @actor)
      approval.update!(
        approver_role: membership.role,
        state: "approved",
        note: @note,
        approved_at: Time.current
      )
      @ceremony.update!(state: "approved") if @ceremony.approval_quorum_met?
      approval
    end
  end
end
