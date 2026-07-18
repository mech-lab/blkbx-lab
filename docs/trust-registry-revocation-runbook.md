# Trust Registry & Revocation Operations Runbook

This runbook covers the operational procedures for managing the trust registry and revocation lists in production MAND8 deployments.

## Overview

The trust registry and revocation system provides cryptographic trust anchors for verifying MAND8 receipts. The system uses two primary artifacts:

- **Trust Registry** (`ink.trust-registry.v2`) — Authoritative list of trusted issuer keys with metadata
- **Revocation List** (`ink.revocations.v2`) — Signed list of revoked keys with reasons and timestamps

Both artifacts are signed by a trust authority key and verified by all verifiers.

---

## 1. Key Bootstrap

### 1.1 Generate Trust Authority Key Pair

```bash
# Generate Ed25519 key pair for trust authority
ink-cli key generate --output-dir ./trust-authority --key-id ta-001

# Output:
# - trust-authority/ta-001.ed25519.key (private, 0600 perms)
# - trust-authority/ta-001.ed25519.pub (public)
```

### 1.2 Initialize Trust Registry

```bash
# Create initial trust registry with trust authority as signer
ink-cli trust-registry init \
  --authority-key ./trust-authority/ta-001.ed25519.key \
  --output ./trust-registry.v2.json \
  --registry-version "1.0.0"
```

### 1.3 Add Initial Issuers

```bash
# Add production issuer to registry
ink-cli trust-registry add-issuer \
  --registry ./trust-registry.v2.json \
  --authority-key ./trust-authority/ta-001.ed25519.key \
  --key-id "ed25519:abc123..." \
  --issuer-name "MAND8 Production Issuer" \
  --org-name "BLKBX Lab" \
  --usage "receipt_signing" \
  --state "active" \
  --valid-from "2026-01-01T00:00:00Z" \
  --valid-until "2027-01-01T00:00:00Z"

# Add backup issuer
ink-cli trust-registry add-issuer \
  --registry ./trust-registry.v2.json \
  --authority-key ./trust-authority/ta-001.ed25519.key \
  --key-id "ed25519:def456..." \
  --issuer-name "MAND8 Backup Issuer" \
  --org-name "BLKBX Lab" \
  --usage "receipt_signing" \
  --state "standby" \
  --valid-from "2026-01-01T00:00:00Z" \
  --valid-until "2027-01-01T00:00:00Z"
```

### 1.4 Initialize Revocation List

```bash
# Create empty revocation list signed by trust authority
ink-cli revocation-list init \
  --authority-key ./trust-authority/ta-001.ed25519.key \
  --output ./revocations.v2.json \
  --list-version "1.0.0"
```

### 1.5 Deploy to Production

```bash
# Copy to production config directory
mkdir -p /etc/inkreceipts
cp trust-registry.v2.json /etc/inkreceipts/
cp revocations.v2.json /etc/inkreceipts/
cp trust-authority/ta-001.ed25519.pub /etc/inkreceipts/trust-authority.pub

# Configure signer to use remote registry
ink-cli signer configure \
  --backend remote_kms_v1 \
  --trust-registry-url https://trust.example.com/trust-registry.v2.json \
  --revocations-url https://trust.example.com/revocations.v2.json \
  --pinned-trust-authority-public-key /etc/inkreceipts/trust-authority.pub
```

---

## 2. Key Rotation

### 2.1 Scheduled Rotation (Annual)

```bash
# 1. Generate new issuer key pair
ink-cli key generate --output-dir ./keys/new-issuer --key-id issuer-002

# 2. Add new issuer to trust registry (standby state)
ink-cli trust-registry add-issuer \
  --registry ./trust-registry.v2.json \
  --authority-key ./trust-authority/ta-001.ed25519.key \
  --key-id "ed25519:newkey..." \
  --issuer-name "MAND8 Production Issuer v2" \
  --org-name "BLKBX Lab" \
  --usage "receipt_signing" \
  --state "standby" \
  --valid-from "2026-07-01T00:00:00Z" \
  --valid-until "2027-07-01T00:00:00Z"

# 3. Deploy updated registry
ink-cli trust-registry sign \
  --registry ./trust-registry.v2.json \
  --authority-key ./trust-authority/ta-001.ed25519.key \
  --output ./trust-registry.v2.json.signed

# 4. Update signer config to use new key (staged)
ink-cli signer stage-key \
  --key-id "ed25519:newkey..." \
  --secret-key ./keys/new-issuer/issuer-002.ed25519.key

# 5. At rotation time, promote new key to active
ink-cli trust-registry update-issuer \
  --registry ./trust-registry.v2.json \
  --authority-key ./trust-authority/ta-001.ed25519.key \
  --key-id "ed25519:oldkey..." \
  --state "retired"

ink-cli trust-registry update-issuer \
  --registry ./trust-registry.v2.json \
  --authority-key ./trust-authority/ta-001.ed25519.key \
  --key-id "ed25519:newkey..." \
  --state "active"

# 6. Sign and deploy updated registry
ink-cli trust-registry sign \
  --registry ./trust-registry.v2.json \
  --authority-key ./trust-authority/ta-001.ed25519.key \
  --output ./trust-registry.v2.json.signed

# 7. Activate new key in signer
ink-cli signer activate-staged-key
```

### 2.2 Emergency Rotation (Compromise)

See Section 4: Compromise Response.

---

## 3. Key Revocation

### 3.1 Standard Revocation (Key Retirement)

```bash
# Revoke a key that is being retired (not compromised)
ink-cli revocation-list add \
  --list ./revocations.v2.json \
  --authority-key ./trust-authority/ta-001.ed25519.key \
  --key-id "ed25519:oldkey..." \
  --reason "scheduled_retirement" \
  --revoked-at "2026-07-01T00:00:00Z"

# Sign and deploy
ink-cli revocation-list sign \
  --list ./revocations.v2.json \
  --authority-key ./trust-authority/ta-001.ed25519.key \
  --output ./revocations.v2.json.signed

# Deploy to production
cp revocations.v2.json.signed /etc/inkreceipts/revocations.v2.json
```

### 3.2 Verify Revocation Status

```bash
# Check if a key is revoked
ink-cli revocation-list check \
  --list ./revocations.v2.json \
  --key-id "ed25519:oldkey..."

# Output: REVOKED (reason: scheduled_retirement, revoked_at: 2026-07-01T00:00:00Z)
```

---

## 4. Compromise Response

### 4.1 Immediate Actions (T+0 to T+15 min)

```bash
# 1. REVOKE the compromised key IMMEDIATELY
ink-cli revocation-list add \
  --list ./revocations.v2.json \
  --authority-key ./trust-authority/ta-001.ed25519.key \
  --key-id "ed25519:compromised..." \
  --reason "key_compromise" \
  --revoked-at "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 2. Sign and deploy emergency revocation list
ink-cli revocation-list sign \
  --list ./revocations.v2.json \
  --authority-key ./trust-authority/ta-001.ed25519.key \
  --output ./revocations.v2.json.signed

# 3. Deploy to ALL verifiers immediately (push or CDN purge)
cp revocations.v2.json.signed /etc/inkreceipts/revocations.v2.json
# OR: aws s3 cp revocations.v2.json.signed s3://trust-cdn/revocations.v2.json --cache-control "max-age=60"
```

### 4.2 Short-term Actions (T+15 min to T+1 hour)

```bash
# 1. Generate emergency replacement key
ink-cli key generate --output-dir ./keys/emergency --key-id issuer-emergency

# 2. Add emergency issuer to trust registry (active immediately)
ink-cli trust-registry add-issuer \
  --registry ./trust-registry.v2.json \
  --authority-key ./trust-authority/ta-001.ed25519.key \
  --key-id "ed25519:emergency..." \
  --issuer-name "MAND8 Emergency Issuer" \
  --org-name "BLKBX Lab" \
  --usage "receipt_signing" \
  --state "active" \
  --valid-from "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --valid-until "2026-08-01T00:00:00Z"

# 3. Mark compromised key as revoked in registry
ink-cli trust-registry update-issuer \
  --registry ./trust-registry.v2.json \
  --authority-key ./trust-authority/ta-001.ed25519.key \
  --key-id "ed25519:compromised..." \
  --state "revoked"

# 4. Sign and deploy updated registry
ink-cli trust-registry sign \
  --registry ./trust-registry.v2.json \
  --authority-key ./trust-authority/ta-001.ed25519.key \
  --output ./trust-registry.v2.json.signed

# 5. Deploy to production
cp trust-registry.v2.json.signed /etc/inkreceipts/trust-registry.v2.json
```

### 4.3 Long-term Actions (T+1 hour to T+24 hours)

```bash
# 1. Audit all receipts signed by compromised key
ink-cli receipt audit \
  --key-id "ed25519:compromised..." \
  --since "2026-01-01T00:00:00Z" \
  --output ./compromised-receipts.json

# 2. Notify affected parties (partners, regulators)
# Use the compromised-receipts.json to identify impacted receipts

# 3. Generate proper replacement key with full validity period
ink-cli key generate --output-dir ./keys/replacement --key-id issuer-003

# 4. Add proper replacement to registry
ink-cli trust-registry add-issuer \
  --registry ./trust-registry.v2.json \
  --authority-key ./trust-authority/ta-001.ed25519.key \
  --key-id "ed25519:replacement..." \
  --issuer-name "MAND8 Production Issuer v3" \
  --org-name "BLKBX Lab" \
  --usage "receipt_signing" \
  --state "active" \
  --valid-from "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --valid-until "2027-07-18T00:00:00Z"

# 5. Retire emergency key
ink-cli trust-registry update-issuer \
  --registry ./trust-registry.v2.json \
  --authority-key ./trust-authority/ta-001.ed25519.key \
  --key-id "ed25519:emergency..." \
  --state "retired"

# 6. Sign and deploy final registry
ink-cli trust-registry sign \
  --registry ./trust-registry.v2.json \
  --authority-key ./trust-authority/ta-001.ed25519.key \
  --output ./trust-registry.v2.json.signed

cp trust-registry.v2.json.signed /etc/inkreceipts/trust-registry.v2.json
```

### 4.4 Post-Incident Review (T+24 hours to T+7 days)

- [ ] Complete incident report with timeline
- [ ] Root cause analysis of compromise
- [ ] Update key management procedures
- [ ] Rotate trust authority key if needed
- [ ] Update runbook with lessons learned

---

## 5. Verification Procedures

### 5.1 Verify Trust Registry Integrity

```bash
# Verify registry signature against pinned trust authority key
ink-cli trust-registry verify \
  --registry ./trust-registry.v2.json \
  --pinned-authority-key /etc/inkreceipts/trust-authority.pub
```

### 5.2 Verify Revocation List Integrity

```bash
# Verify revocation list signature
ink-cli revocation-list verify \
  --list ./revocations.v2.json \
  --trust-registry ./trust-registry.v2.json
```

### 5.3 End-to-End Verification Test

```bash
# Test that a receipt signed by active issuer verifies
ink-cli verify \
  --receipt ./test-receipt.v2.json \
  --trust-registry ./trust-registry.v2.json \
  --revocation-list ./revocations.v2.json

# Test that a receipt signed by revoked key fails
ink-cli verify \
  --receipt ./revoked-receipt.v2.json \
  --trust-registry ./trust-registry.v2.json \
  --revocation-list ./revocations.v2.json
# Expected: FAIL with REVOKED_ISSUER_KEY
```

---

## 6. Monitoring & Alerting

### 6.1 Key Expiry Monitoring

```bash
# Check for keys expiring within 30 days
ink-cli trust-registry check-expiry \
  --registry ./trust-registry.v2.json \
  --warning-days 30
```

### 6.2 Revocation List Freshness

```bash
# Alert if revocation list older than 24 hours
ink-cli revocation-list check-freshness \
  --list ./revocations.v2.json \
  --max-age-hours 24
```

### 6.3 Health Checks

```bash
# Full trust infrastructure health check
ink-cli doctor --check-trust-infrastructure
```

---

## 7. File Locations & Permissions

| File | Location | Permissions | Owner |
|------|----------|-------------|-------|
| Trust Authority Private Key | `/etc/inkreceipts/trust-authority.key` | 0600 | root:ink |
| Trust Authority Public Key | `/etc/inkreceipts/trust-authority.pub` | 0644 | root:ink |
| Trust Registry | `/etc/inkreceipts/trust-registry.v2.json` | 0644 | root:ink |
| Revocation List | `/etc/inkreceipts/revocations.v2.json` | 0644 | root:ink |
| Signer Config | `/etc/inkreceipts/signer-config.json` | 0640 | root:ink |
| Issuer Private Key | `/etc/inkreceipts/keys/active.ed25519.key` | 0600 | root:ink |
| Issuer Public Key | `/etc/inkreceipts/keys/active.ed25519.pub` | 0644 | root:ink |

---

## 8. Quick Reference Commands

```bash
# View current trust registry
ink-cli trust-registry view --registry /etc/inkreceipts/trust-registry.v2.json

# View current revocation list
ink-cli revocation-list view --list /etc/inkreceipts/revocations.v2.json

# Check issuer status
ink-cli trust-registry get-issuer --registry /etc/inkreceipts/trust-registry.v2.json --key-id "ed25519:..."

# Emergency revocation (single command)
ink-cli emergency-revoke \
  --key-id "ed25519:compromised..." \
  --reason "key_compromise" \
  --trust-registry /etc/inkreceipts/trust-registry.v2.json \
  --revocation-list /etc/inkreceipts/revocations.v2.json \
  --authority-key /etc/inkreceipts/trust-authority.key
```

---

## 9. Escalation Contacts

| Role | Contact | Escalation Time |
|------|---------|-----------------|
| Primary Operator | ops-primary@blkbxlab.com | T+0 |
| Secondary Operator | ops-secondary@blkbxlab.com | T+15 min |
| Security Lead | security@blkbxlab.com | T+30 min |
| CTO | cto@blkbxlab.com | T+1 hour |
| Legal/Compliance | legal@blkbxlab.com | T+2 hours |

---

*Last Updated: 2026-07-18*
*Version: 1.0.0*
*Classification: Internal - Operational*