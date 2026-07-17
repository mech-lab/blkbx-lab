class WorkspacePolicy < ApplicationPolicy
  def index?
    user.present?
  end

  def show?
    member_of?(record.organization)
  end

  def create?
    admin_for?(record.organization)
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
