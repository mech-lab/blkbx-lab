Rails.application.routes.draw do
  get "up" => "rails/health#show", as: :rails_health_check

  devise_for :users

  namespace :accounts do
    resources :session_handoffs, only: :create do
      collection do
        get :consume
      end
    end
  end

  namespace :api do
    namespace :v1 do
      resources :receipts, only: [:create, :show, :index]
      resources :verifications, only: [:create]
      resources :evidence_bundles, only: [:create, :show, :index]
      resources :trust_registries, only: [:create, :show, :index]
      resources :api_credentials, only: [:create, :show, :index, :destroy]

      resources :organizations, only: [:show, :index, :create, :update] do
        resources :workspaces, only: [:show, :index, :create, :update] do
          member do
            post :select
            post :seed_demo
          end
        end
      end

      namespace :blkbxs do
        resources :control_receipts, only: [:create, :show, :index]
        resources :underwriting_decision_receipts, only: [:create, :show, :index]
        resources :vendor_review_bundles, only: [:create, :show, :index]
        resources :review_requests, only: [:create, :show, :index, :update]
      end

      namespace :mand8 do
        resource :dashboard, only: :show
        resources :insurability_receipts, only: [:create, :show, :index]
        resources :authority_receipts, only: [:create, :show, :index]
        resources :incident_receipts, only: [:create, :show, :index]
        resources :renewal_bundles, only: [:create, :show, :index]
        resources :carrier_review_requests, only: [:create, :show, :index, :update]
      end

      namespace :due do
        resources :reasoning_receipts, only: [:create, :show, :index]
        resources :authority_receipts, only: [:create, :show, :index]
        resources :privilege_receipts, only: [:create, :show, :index]
        resources :disclosure_receipts, only: [:create, :show, :index]
        resources :defensibility_bundles, only: [:create, :show, :index]
        resources :matter_exports, only: [:create, :show, :index]
      end
    end
  end

  authenticated :user do
    root to: "dashboards#show", as: :authenticated_root
    resource :dashboard, only: :show
  end

  root to: "home#show"

  get "pricing", to: "pages#pricing"
  get "docs", to: "pages#docs"
  get "verify", to: "pages#verify"
  get "status", to: "pages#status"
  resources :shared_bundles, only: :show do
    resources :download_events, only: :create
  end
  resources :review_requests, only: :update
end
