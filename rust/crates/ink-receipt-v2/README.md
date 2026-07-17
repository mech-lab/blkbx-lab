# INK Receipt v2 Verifier Surface

This crate verifies the current public `v2` receipt and bundle artifacts used by the shipped BLKBX Lab flow.

## Artifact Scope

- `ink_receipt.v2.json`
- optional `ink_manifest.v2.json`
- optional controls payloads
- optional trust registry, revocation list, and verification policy files

## Native CLI Entry Points

```bash
ink receipt --receipt ink_receipt.v2.json
ink bundle --receipt ink_receipt.v2.json --manifest ink_manifest.v2.json
ink policy --policy verify-policy.json
ink-tui
ink-tui verify --receipt ink_receipt.v2.json
```

## Boundary

This crate is part of the native verification path. It does not change the public install package name, the primary `blkbx-lab` docs surface, or the current `v2` artifact contract.
