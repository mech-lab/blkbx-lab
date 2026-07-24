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
      resources :signing_keys, only: [:create, :show, :index]
      resources :key_ceremonies, only: [:create, :show, :index] do
        member do
          post :approve
          post :activate
          post :retire
          post :revoke
          post :publish
        end
      end
      resources :trust_publications, only: [:show, :index] do
        collection do
          get :current
        end
      end
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
        resource :dashboard, only: :show
        resource :verifier_artifacts, only: :show
        resources :loan_cases, only: [:index, :show, :create] do
          scope module: :loan_cases do
            resources :evidence_events, only: [:index, :create]
            resources :ink_receipts, only: [:index]
            resources :verification_runs, only: [:index, :show, :create]
            resources :evidence_bundles, only: [:index, :show, :create]
            resources :exports, only: [:create, :show]
          end
        end
        resources :control_receipts, only: [:create, :show, :index]
        resources :underwriting_decision_receipts, only: [:create, :show, :index]
        resources :ubr_receipts, only: [:create, :show, :index]
        resources :ubr_bundles, only: [:create, :show, :index]
        resources :vendor_review_bundles, only: [:create, :show, :index]
        resources :review_requests, only: [:create, :show, :index, :update]
      end

      namespace :mand8 do
        resource :dashboard, only: :show
        resource :verifier_artifacts, only: :show
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

  namespace :blkbxs do
    namespace :sprint do
      root to: "dashboards#show"
      resource :dashboard, only: :show
      resources :loan_cases, only: [:index, :show] do
        member do
          get :timeline
          get :receipt_graph
          get :verification
          get :objections
          get :exports
        end
      end
    end
  end

  root to: "home#show"

  get "pricing", to: "pages#pricing"
  get "docs", to: "pages#docs"
  get "verify", to: redirect("/verify/index.html")
  get "verify/index.html", to: "verify#show"
  get "verify/*path", to: "verify#asset"
  get "status", to: "pages#status"
  resources :shared_bundles, only: :show do
    resources :download_events, only: :create
  end
  resources :review_requests, only: :update
end
