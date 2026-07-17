class Current < ActiveSupport::CurrentAttributes
  attribute :product
  attribute :brand
  attribute :organization
  attribute :workspace
  attribute :environment
  attribute :user
  attribute :request_id
  attribute :api_credential
  attribute :identity_host

  def product_name
    product.to_s
  end

  def product_type
    product
  end
end
