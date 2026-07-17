class SdkInstallation < ApplicationRecord
  belongs_to :organization
  belongs_to :workspace
  belongs_to :application, optional: true

  validates :organization, :workspace, :sdk_name, :sdk_version, :installation_kind, presence: true
end
