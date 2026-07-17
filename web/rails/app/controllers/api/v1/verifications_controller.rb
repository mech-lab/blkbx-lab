module Api
  module V1
    class VerificationsController < BaseController
      def create
        return unless require_capability!("verifications:create")

        receipt = Current.workspace.receipts.find(params.require(:receipt_id))
        policy = Current.workspace.verification_policies.find(params.require(:verification_policy_id))
        run = Ink::VerifyReceipt.call(receipt: receipt, verification_policy: policy)
        render_record(run, status: :created)
      end
    end
  end
end
