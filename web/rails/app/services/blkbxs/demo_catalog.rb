module Blkbxs
  class DemoCatalog
    CANONICAL_EXTERNAL_SCENARIO = "smb_loan_demo".freeze
    ROOT = Rails.root.join("..", "..").expand_path.freeze
    FIXTURE_PATH = ROOT.join("python", "blkbx_lab", "products", "blkbxs", "fixtures", "smb_loan_demo.json").freeze

    def self.available_scenarios
      [
        {
          key: CANONICAL_EXTERNAL_SCENARIO,
          name: "SMB loan conditional approval",
          source_path: FIXTURE_PATH.to_s
        }
      ]
    end

    def self.fetch(scenario)
      raise ArgumentError, "Unknown BLKBXS demo scenario: #{scenario}" unless scenario == CANONICAL_EXTERNAL_SCENARIO

      JSON.parse(File.read(FIXTURE_PATH))
    end
  end
end
