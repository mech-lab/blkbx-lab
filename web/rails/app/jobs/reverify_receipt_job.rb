class ReverifyReceiptJob < ApplicationJob
  queue_as :default

  def perform(receipt_id)
    receipt = Receipt.find(receipt_id)
    policy = receipt.workspace.verification_policies.active.first
    return unless policy

    Ink::VerifyReceipt.call(receipt: receipt, verification_policy: policy)
  end
end
