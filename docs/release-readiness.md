# Release Readiness Checklist

Current shipped truth as of July 22, 2026:

- install package: `mechlab-sdk`
- primary CLI/docs surface: `blkbx-lab`
- primary Python docs surface: `blkbx_lab`
- stable product imports ride through the same root wheel: `blkbxs`, `mand8`, `due`

## Automated Gates

- `python3 scripts/check_release_readiness.py`
- `python3 scripts/check_local_release.py`
- `python3 -m pytest -q tests/test_readme_example.py tests/test_packaging_contracts.py tests/test_release_readiness.py tests/test_mech_lab_product.py tests/test_mech_lab_doctor.py`
- `python3 -m pytest tests/test_blkbxs_ubr.py tests/test_umbrella_product_imports.py tests/p0/test_packaging_contracts.py tests/test_packaging_contracts.py tests/test_brand_release_assets.py`
- `python3 -m ruff check .`

## What the Readiness Script Enforces

- clean git worktree for release candidates unless explicitly skipped
- active docs do not claim `blkbx-lab` is the install package
- active docs do not use `v1` public artifact filenames
- active docs do not reference retired CLI verbs outside the shipped command set
- relative markdown links resolve inside the active docs surface
- release workflow uses the authored release template and PyPI trusted publishing
- Qwen validation report keeps workstation-specific absolute paths inside the reproducibility appendix

## Manual Checks Before Tagging

- confirm the repository README renders correctly on GitHub
- confirm the docs hub and archive index links resolve
- confirm the release draft uses [`.github/RELEASE_TEMPLATE.md`](../.github/RELEASE_TEMPLATE.md)
- confirm the repository social preview uses [`assets/brand/og-card.png`](../assets/brand/og-card.png)
- confirm the packaging-facing copy still matches [`docs/pypi.md`](pypi.md)
- confirm a fresh install exposes `blkbx_lab`, `blkbxs`, `mand8`, and `due`
- confirm BLKBXS UBR docs describe the Python-generated SMB loan fixture and do not imply Rails hand-authors a second copy
- confirm Rails UBR receipt creation requires `INK_ISSUER_SERVICE_URL` and rolls back when `ink.receipt.v2` signing is unavailable
- confirm UBR demo verifier reports and synthetic Ed25519 labels are documented as evidence only, not the trust root

## Source-of-Truth Docs

- [`README.md`](../README.md)
- [`docs/README.md`](README.md)
- [`docs/pypi.md`](pypi.md)
- [`docs/mvp-cli-api-contract.md`](mvp-cli-api-contract.md)
- [`docs/public-object-spec.md`](public-object-spec.md)
- [`docs/bank-verifiable-receipts.md`](bank-verifiable-receipts.md)
- [`docs/mand8-procurement-readiness.md`](mand8-procurement-readiness.md)
- [`docs/proofmail-hosted-workflow.md`](proofmail-hosted-workflow.md)
- [`docs/research/qwen35-validation-report.md`](research/qwen35-validation-report.md)

## Historical Material

Historical planning and exploratory documents live under [`docs/archive/`](archive/README.md). They should stay out of the primary onboarding path until rewritten against the shipped surface.
