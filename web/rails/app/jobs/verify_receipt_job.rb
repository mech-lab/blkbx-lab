class VerifyReceiptJob < ApplicationJob
  queue_as :default

  def perform(receipt_id, verification_policy_id, evidence_bundle_id = nil)
    receipt = Receipt.find(receipt_id)
    policy = VerificationPolicy.find(verification_policy_id)
    bundle = evidence_bundle_id.present? ? EvidenceBundle.find(evidence_bundle_id) : nil
    Ink::VerifyReceipt.call(receipt: receipt, verification_policy: policy, evidence_bundle: bundle)
  end
end
