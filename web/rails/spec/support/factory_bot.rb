RSpec.configure do |config|
  config.before(:suite) do
    FactoryBot.reload
  end
end
