class VerifyController < ApplicationController
  VERIFY_ROOT = Rails.root.join("..", "verify").expand_path.freeze

  skip_forgery_protection

  def show
    render file: VERIFY_ROOT.join("index.html"), layout: false, content_type: "text/html"
  end

  def asset
    candidate = VERIFY_ROOT.join(params[:path].to_s).expand_path
    root = "#{VERIFY_ROOT}/"
    return render plain: "Not Found", status: :not_found unless candidate.to_s.start_with?(root) && candidate.file?

    send_file candidate, disposition: "inline", type: content_type_for(candidate.extname)
  end

  private

  def content_type_for(extension)
    case extension
    when ".css" then "text/css"
    when ".js" then "text/javascript"
    when ".json" then "application/json"
    when ".wasm" then "application/wasm"
    when ".md" then "text/markdown"
    else
      Rack::Mime.mime_type(extension, "application/octet-stream")
    end
  end
end
