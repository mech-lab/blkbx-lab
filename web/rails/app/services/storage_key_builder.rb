class StorageKeyBuilder
  def self.call(kind:, organization_id:, record_id:, filename:)
    case kind.to_sym
    when :receipt
      "receipts/#{organization_id}/#{record_id}/#{filename}"
    when :payload
      "payloads/#{organization_id}/#{record_id}/#{filename}"
    when :artifact
      "artifacts/#{organization_id}/#{record_id}/#{filename}"
    when :bundle
      "bundles/#{organization_id}/#{record_id}/#{filename}"
    else
      "#{kind}/#{organization_id}/#{record_id}/#{filename}"
    end
  end
end
