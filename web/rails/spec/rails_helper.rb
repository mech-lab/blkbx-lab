ENV["RAILS_ENV"] ||= "test"
require File.expand_path("../config/environment", __dir__)
abort("The Rails environment is running in production mode!") if Rails.env.production?

require "rspec/rails"

Dir[Rails.root.join("spec/support/**/*.rb")].sort.each { |file| require file }

begin
  # Allow DB-less smoke validation for scaffold routing/service checks.
  ActiveRecord::Migration.maintain_test_schema! unless ENV["SKIP_DB_SCHEMA_CHECK"] == "1"
rescue ActiveRecord::PendingMigrationError => error
  abort error.to_s.strip
end

skip_db_schema_check = ENV["SKIP_DB_SCHEMA_CHECK"] == "1"

RSpec.configure do |config|
  config.include FactoryBot::Syntax::Methods
  config.include Devise::Test::IntegrationHelpers, type: :request
  config.fixture_paths = [Rails.root.join("spec/fixtures").to_s]
  config.use_transactional_fixtures = !skip_db_schema_check
  config.use_active_record = !skip_db_schema_check
  config.infer_spec_type_from_file_location!
  config.filter_rails_from_backtrace!
end
