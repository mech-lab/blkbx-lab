# Migration from `mech-lab`

BLKBX Lab is the product name, but the shipped install package is `mechlab-sdk`.

## Name Mapping

| Older or compatibility name | Current guidance |
| --- | --- |
| install command using `mech-lab` naming | install `mechlab-sdk` |
| `mechlab` CLI | use `blkbx-lab` in primary docs and examples |
| `mech_lab` Python namespace | use `blkbx_lab` in primary docs and examples |

## Migration Rule

- For install instructions, use `mechlab-sdk`.
- For new quickstarts, examples, and API narration, use `blkbx-lab` and `blkbx_lab`.
- Keep compatibility aliases only where older automation or migration notes need them.

## Artifact Rule

Active docs should refer only to the shipped artifact set:

- `ink_manifest.v2.json`
- `ink_receipt.v2.json`
- `receipt_comparison.v2.json`

## Where to Link

- public onboarding: [docs hub](README.md)
- contract details: [CLI and API contract](mvp-cli-api-contract.md)
- compatibility details: [migration and compatibility notes](migration-compatibility.md)
