class OrganizationPolicy < ApplicationPolicy
  def index?
    user.present?
  end

  def show?
    member_of?(record)
  end

  def create?
    user.present?
  end

  def update?
    admin_for?(record)
  end

  def destroy?
    user&.owner_of?(record)
  end

  class Scope < Scope
    def resolve
      user ? user.organizations : scope.none
    end
  end
end
