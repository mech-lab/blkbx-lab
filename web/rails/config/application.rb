require_relative "boot"

require "rails"
require "active_model/railtie"
require "active_job/railtie"
require "active_record/railtie"
require "active_storage/engine"
require "action_controller/railtie"
require "action_mailer/railtie"
require "action_view/railtie"
require "action_cable/engine"

Bundler.require(*Rails.groups)
require_relative "../lib/rack/domain_product_resolver"

module InkReceipts
  class Application < Rails::Application
    config.load_defaults 7.1

    config.middleware.use Rack::DomainProductResolver
    config.autoload_paths << Rails.root.join("lib")
    config.eager_load_paths << Rails.root.join("lib")

    config.active_job.queue_adapter = :solid_queue
    config.time_zone = "UTC"
    config.generators.system_tests = nil

    config.generators do |g|
      g.orm :active_record, migration: true
      g.test_framework :rspec
      g.factory_bot dir: "spec/factories"
    end
  end
end
