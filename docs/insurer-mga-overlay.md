# MAND8 Insurer/MGA Procurement Overlay

This is the primary buyer overlay for the [MAND8 procurement-readiness](mand8-procurement-readiness.md) phase. It is built from the shared evidence core and the canonical `lloyds_incident_to_renewal` reviewer packet.

## 1. Evidence Requirements
- Primary evidence: Portable verifier packets (ink.receipt.v2) with bundled MAND8 bundles
- Required metadata: Risk class, insured value, policy conditions, binder references
- Trust registry/revocation list integration for key trust validation
- Incident receipts for cyber event tracking (when applicable)
- Human review documentation for delegated authority validation

## 2. Workflow Integration
- MAND8 handoff to insurer/MGA via standardized bundle export
- Evidence validation against MAND8 risk_receipt.v1 schema upon receipt
- Automated verification via `ink receipt` CLI with trust policy
- Browser verifier compatibility for visual inspection
- Integration with insurer/MGA existing risk assessment workflows
- API endpoints for programmatic bundle ingestion and validation

## 3. Security Considerations
- Trust boundary enforcement: Native Rust verification as trust root
- No JavaScript-based trust assumptions in verification path
- Offline verification capability for air-gapped environments
- Compliance with ink.receipt.v2 schema and cryptographic standards
- Key rotation awareness through trust registry validity periods
- Revocation checking for compromised keys

## 4. Data Model Extensions
- Procurement-specific metadata fields in bundle exports
- Loss history integration with MAND8 cyber underwriting data
- Exposure unit mapping to insurer/MGA risk categorization
- Control observation alignment with insurer/MGA control frameworks

## 5. Validation Rules
- Mandatory trust registry verification for all incoming bundles
- Revocation list check for signer key validity
- Schema validation against MAND8 risk_receipt.v1
- Bundle type validation (underwriting_evidence_bundle, renewal_evidence_pack)
- Audience validation (lloyds_underwriter, carrier_innovation_team)

## 6. Pilot Request Template
- Insurance/MGA partnership proposal document
- Verification workflow diagram showing trust boundaries
- Security assessment checklist (SOC 2, ISO 27001 considerations)
- Pilot success criteria: 
  - 95%+ automated verification rate
  - <5 minute average verification time
  - Zero trust boundary violations
  - Compatible with existing risk assessment tools

## 7. Implementation Roadmap
Phase 1: Bundle ingestion and basic validation
Phase 2: Trust registry integration and revocation checking
Phase 3: Advanced analytics integration with exposure data
Phase 4: API automation and webhook notifications
Phase 5: Full production deployment with monitoring
