module Workflows
  class CreateReviewRequest
    def self.call(options = {})
      new(options).call
    end

    def initialize(options = {})
      @organization = options.fetch(:organization)
      @workspace = options.fetch(:workspace)
      @evidence_bundle = options.fetch(:evidence_bundle)
      @title = options.fetch(:title)
      @reviewer_email = options.fetch(:reviewer_email)
      @reviewer_name = options.fetch(:reviewer_name)
      @reviewer_role = options.fetch(:reviewer_role)
      @actor = options[:actor]
      @customer_project = options[:customer_project]
      @workflow_run = options[:workflow_run]
    end

    def call
      reviewer = Reviewer.find_or_create_by!(
        organization: @organization,
        workspace: @workspace,
        email: @reviewer_email
      ) do |record|
        record.name = @reviewer_name
        record.role = @reviewer_role
      end

      review_request = ReviewRequest.create!(
        organization: @organization,
        workspace: @workspace,
        evidence_bundle: @evidence_bundle,
        workflow_run: @workflow_run,
        customer_project: @customer_project,
        reviewer: reviewer,
        title: @title,
        status: "pending",
        requested_at: Time.current
      )

      shared_bundle = SharedBundle.create!(
        organization: @organization,
        workspace: @workspace,
        evidence_bundle: @evidence_bundle,
        review_request: review_request,
        name: "#{@title} portal",
        status: "active",
        expires_at: 14.days.from_now
      )

      IssuePortalAccessJob.perform_later(shared_bundle.id, reviewer.id, @actor&.id)
      AuditEvent.record!(
        "bundle.shared",
        auditable: shared_bundle,
        organization: @organization,
        workspace: @workspace,
        user: @actor,
        request_id: Current.request_id,
        resulting_state: shared_bundle.attributes
      )

      [review_request, shared_bundle]
    end
  end
end
