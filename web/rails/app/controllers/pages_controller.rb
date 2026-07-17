class PagesController < ApplicationController
  def pricing
    render json: {
      plans: Plan.active.order(:price_cents).map { |plan| plan.slice(:name, :product_type, :price_cents, :billing_interval, :features) }
    }
  end

  def docs
    render json: { docs_url: "/docs", product: Current.product }
  end

  def verify
    render json: { verifier: "external_wasm", product: :ink, host: request.host }
  end

  def status
    render json: { status: "ok", date: Date.new(2026, 7, 17) }
  end
end
