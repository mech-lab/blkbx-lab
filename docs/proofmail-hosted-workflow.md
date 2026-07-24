# ProofMail Hosted Workflow

ProofMail is the hosted delivery workflow for MAND8 reviewer packets. It is not the trust root; the portable receipt and independent verifier remain the trust root.

## Contracts

The Rust `ink-proofmail` crate defines four hosted workflow contracts:

- `proofmail.packet.v1` packet manifest: packet id, issuer, receipt id, receipt hash, attachment references, and packet integrity hash.
- `proofmail.recipients.v1` recipient manifest: recipients, reviewer roles, delivery policy, retry policy, and encryption policy.
- delivery audit entries: immutable per-attempt records with recipient id, attempt number, delivery status, adapter response, error, and message id.
- send status: packet-level delivery summary with per-recipient status counts.

## Delivery Boundary

ProofMail composes the exact packet that is sent and stores immutable hashes for replay and audit. SMTP and transactional-email adapters implement the same `EmailAdapter` contract so delivery can be configured without changing the packet contract.

The verifier packet still contains the portable `ink.receipt.v2` artifact set. A reviewer must be able to verify locally without trusting ProofMail, Rails, or a hosted dashboard.

## Release Gate

ProofMail release readiness requires:

- packet creation tests for receipt and attachment hash stability
- send-status tests for accepted, rejected, and failed recipients
- audit replay tests from the stored packet
- adapter conformance tests for SMTP and transactional API implementations
- attachment hash mismatch tests before replay or resend
