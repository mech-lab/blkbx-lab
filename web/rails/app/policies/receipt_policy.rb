class ReceiptPolicy < ApplicationPolicy
  def index?
    member_of?(record.organization)
  end

  def show?
    member_of?(record.organization)
  end

  def create?
    member_of?(record.organization) && user&.can_access_workspace?(record.workspace)
  end

  def update?
    admin_for?(record.organization)
  end

  def destroy?
    user&.owner_of?(record.organization)
  end

  class Scope < Scope
    def resolve
      user ? scope.where(organization: user.organizations) : scope.none
    end
  end
end
