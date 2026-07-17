module Api
  module V1
    class BaseController < Api::BaseController
      private

      def render_record(record, status: :ok, extra: {})
        render json: record.as_json.merge(extra), status: status
      end

      def render_collection(scope)
        render json: scope.map(&:as_json)
      end
    end
  end
end
