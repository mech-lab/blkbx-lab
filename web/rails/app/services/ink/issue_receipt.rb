module Ink
  class IssueReceipt
    def self.call(options = {})
      Workflows::CreateReceipt.call(options)
    end
  end
end
