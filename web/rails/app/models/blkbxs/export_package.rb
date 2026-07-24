module Blkbxs
  class ExportPackage < ApplicationRecord
    self.table_name = "blkbxs_export_packages"

    belongs_to :loan_case, class_name: "Blkbxs::LoanCase"
    belongs_to :evidence_bundle, optional: true

    validates :loan_case, :package_type, :status, presence: true
    validates :status, inclusion: { in: %w[pending ready failed] }
  end
end
