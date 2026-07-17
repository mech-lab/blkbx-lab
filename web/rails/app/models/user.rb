class User < ApplicationRecord
  devise :database_authenticatable, :registerable,
           :recoverable, :rememberable, :validatable,
           :confirmable, :timeoutable, :trackable

  has_many :memberships, dependent: :destroy
  has_many :organizations, through: :memberships
  has_many :workspaces, through: :organizations
  has_many :reviewers, dependent: :nullify
  has_many :approvals, dependent: :nullify
  has_many :audit_events, dependent: :nullify
  has_many :session_handoffs, dependent: :destroy

  validates :email, presence: true, uniqueness: true

  def current_organization
    Current.organization
  end

  def current_workspace
    Current.workspace
  end

  def current_product
    Current.product
  end

  def owner_of?(organization)
    memberships.exists?(organization: organization, role: "owner")
  end

  def admin_of?(organization)
    memberships.exists?(organization: organization, role: ["owner", "administrator"])
  end

  def member_of?(organization)
    memberships.exists?(organization: organization)
  end

  def can_access_workspace?(workspace)
    member_of?(workspace.organization)
  end
end
