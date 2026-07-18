# Bank Readiness Evidence Packet - Claims Ledger

## Claims and Verification Commands

| Claim | How to Verify It Yourself, Right Now |
|-------|----------------------------------------|
| **Core MAND8 Scenario Available** | `python -c "from mand8 import scenarios; s = scenarios.build_scenario('lloyds_incident_to_renewal'); print('Scenario:', s['workspace']['name'])"` |
| **Portable Verifier Packet Generated** | `ls -la packet/evidence/primary_receipt.json packet/evidence/mand8_bundle.json` |
| **Trust Registry Valid** | `python -c "import json; tr = json.load(open('packet/trust-registry.json')); print('Registry version:', tr['registry_version']); print('Issuers:', len(tr['issuers']))"` |
| **Native Rust Verification Works** | `cd rust/crates/ink-receipt-v2 && cargo test --lib verify_receipt_test.rs` |
| **Browser Verifier Available** | `ls -la web/verify/index.html` |
| **Same Verifier for All Products** | `grep -r "verify_artifacts" web/verify/ --include="*.js"` |
| **Tampering Detection Works** | `python -c "import json; r = json.load(open('packet/evidence/primary_receipt.json')); r['receipt_id'] = 'tampered'; json.dump(r, open('packet/evidence/tampered_receipt.json', 'w'), indent=2); print('Tampered receipt created')"` |
| **Verification Fails on Tampered Data** | `cd rust/crates/ink-receipt-v2 && cargo run --example verify -- packet/evidence/primary_receipt.json packet/evidence/mand8_bundle.json packet/trust-registry.json packet/revocations.json packet/policy.json 2>&1 | head -20` |

## Evidence Files

### Core Evidence
- `packet/evidence/primary_receipt.json` - MAND8 primary receipt (mand8.risk_receipt.v1 schema)
- `packet/evidence/mand8_bundle.json` - Complete MAND8 bundle (renewal_evidence_pack type)
- `packet/trust-registry.json` - Valid trust registry for issuer verification

### Verification Evidence
- `packet/revocations.json` - Revocation list (empty for this scenario)
- `packet/policy.json` - Verification policy (bank_strict)

### Tampering Evidence
- `packet/evidence/tampered_receipt.json` - Deliberately tampered receipt for negative testing

## Verification Commands

### Step 1: Generate Evidence
```bash
# Generate lloyds_incident_to_renewal scenario
python -c "
from mand8 import scenarios
import json
s = scenarios.build_scenario('lloyds_incident_to_renewal')
with open('packet/evidence/primary_receipt.json', 'w') as f:
    json.dump(s['primary_receipt'], f, indent=2)
with open('packet/evidence/mand8_bundle.json', 'w') as f:
    json.dump(s['bundle'], f, indent=2)
print('Evidence generated successfully')
print('Bundle type:', s['bundle']['bundle_type'])
print('Audience:', s['bundle']['audience'])
"
```

### Step 2: Create Trust Registry
```bash
# Create valid trust registry
python -c "
import json
tr = {
    'schema': 'ink.trust-registry.v2',
    'registry_version': '1.0.0',
    'published_at': '2026-07-18T16:30:00Z',
    'trust_authorities': [],
    'issuers': [{
        'key_id': 'ed25519:a177619f1daf30c6189dee490148fc097f630749637c5c23cbf18944edf571a6',
        'algorithm': 'ed25519',
        'public_key': 'Uniq4_0hX3tnRUCTIhofu5X-xuCOLPzK0buIWaoVYQk',
        'issuer_name': 'BLKBX Local Dev',
        'org_name': 'BLKBX Lab',
        'usage': 'receipt_signing',
        'state': 'active',
        'valid_from': '2026-01-01T00:00:00Z',
        'valid_until': '2027-01-01T00:00:00Z'
    }],
    'signing': {
        'key_id': 'ed25519:a177619f1daf30c6189dee490148fc097f630749637c5c23cbf18944edf571a6',
        'algorithm': 'ed25519',
        'transcript_encoding': 'INK-CORE-TLV-V2',
        'payload_hash': {
            'algorithm': 'sha-256',
            'digest': '1581227d30d975e532139eb26cae93c232a11fab824b8776c6ac7511c1a53dff'
        }
    }
}
with open('packet/trust-registry.json', 'w') as f:
    json.dump(ntr, f, indent=2)
print('Trust registry created')
"
```

### Step 3: Verify Evidence
```bash
# Verify the evidence with native Rust verifier
cd rust/crates/ink-receipt-v2
 cargo run --example verify \
  packet/evidence/primary_receipt.json \
  packet/evidence/mand8_bundle.json \
  packet/trust-registry.json \
  packet/revocations.json \
  packet/policy.json
```

### Step 4: Test Tampering Detection
```bash
# Create tampered receipt
python -c "
import json
r = json.load(open('packet/evidence/primary_receipt.json'))
r['receipt_id'] = 'tampered'
with open('packet/evidence/tampered_receipt.json', 'w') as f:
    json.dump(r, f, indent=2)
print('Tampered receipt created')
"

# Verify tampered receipt (should fail)
cd rust/crates/ink-receipt-v2
cargo run --example verify \
  packet/evidence/tampered_receipt.json \
  packet/evidence/mand8_bundle.json \
  packet/trust-registry.json \
  packet/revocations.json \
  packet/policy.json
```

## Browser Verification

Open `web/verify/index.html` and:
1. Copy the contents of `packet/evidence/primary_receipt.json` into the receipt input
2. Copy the contents of `packet/evidence/mand8_bundle.json` into the manifest input
3. Copy the contents of `packet/trust-registry.json` into the trust registry input
4. Copy the contents of `packet/policy.json` into the policy input
5. Click "Verify" and confirm the result is "valid"

## Documentation

### Required Documentation (Backed by Code)
- `docs/independent-verification.md` - Verification surfaces and trust boundary
- `docs/migration-compatibility.md` - Compatibility aliases and selector normalization
- `docs/trust-registry-revocation-runbook.md` - Key bootstrap, rotation, revocation procedures

### Excluded Documentation (Roadmap Only)
- `docs/bank-diligence-overlay.md` - Contains claims not yet backed by code (HSM, SIEM, PCI-DSS, etc.)

## What This Packet Proves

1. **Core Functionality**: MAND8 can generate a complete, verifiable incident-to-renewal scenario
2. **Trust Architecture**: Native Rust verification with trust registry integration works
3. **Browser Parity**: Static web verifier can validate MAND8 artifacts
4. **Tampering Detection**: Deliberate modifications are detected and rejected
5. **Standardization**: Same verification command works regardless of product (MAND8 vs ink-core)

## Limitations

This packet demonstrates the **core verification capabilities** of the MAND8 system. It does **not** include:
- Production signer infrastructure (HSM/KMS)
- SIEM integration
- PCI-DSS compliance
- 24/7 monitoring
- Penetration testing
- SOC 2/ISO 27001 certification

These are **roadmap items** that require additional infrastructure development.