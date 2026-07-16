# Release Readiness Checklist

Current alpha verdict:

- the public BLKBX Lab contract is centered on `mechlab-sdk` / `blkbx_lab`
- stable product imports `blkbxs`, `mand8`, and `due` now ride in the same published wheel
- remaining release risk is mostly packaging discipline, signer configuration clarity, and test coverage
- release-facing copy must describe only the shipped product repo, not removed research trees

Automated gates:

- `python scripts/check_release_readiness.py`
- `python scripts/check_local_release.py`
- `python -m ruff check .`
- focused public-contract test suite
- `python3 -m build`
- `python3 -m twine check dist/*`
- fresh-venv wheel and sdist smoke installs

The local v0.9.1 readiness target is the root `mechlab-sdk` distribution only. `products/*` remain source slices and repo organization units, but the stable `blkbxs`, `mand8`, and `due` Python surfaces now ship through that root wheel.

What the readiness check enforces:

- clean git worktree for release candidates
- release-facing docs and templates do not use retired public names or retired artifact filenames
- the Qwen validation report keeps workstation-specific absolute paths inside a reproducibility appendix
- the release workflow consumes the authored release-note template
- the release workflow includes a trusted-publishing job for PyPI through the `pypi` environment

Manual checks before tagging:

- confirm the live GitHub repository metadata matches [`.github/settings.yml`](../.github/settings.yml)
- confirm the GitHub README renders correctly
- confirm the release draft uses [`.github/RELEASE_TEMPLATE.md`](../.github/RELEASE_TEMPLATE.md) and the attached SVG assets render cleanly
- confirm the repository social preview uses [`assets/brand/og-card.png`](../assets/brand/og-card.png)
- confirm the social preview and branded badges are readable in both GitHub light and dark themes
- confirm the PyPI long description still matches [`docs/pypi.md`](pypi.md)
- confirm the PyPI pending publisher is configured for `mechlab-sdk / blkbx-lab / .github/workflows/release.yml / pypi`
- confirm a fresh install exposes `blkbx_lab`, `mech_lab`, `blkbxs`, `mand8`, and `due`
- confirm the extra groups `research`, `experimental`, and `all` resolve in a fresh environment

Current source-of-truth docs:

- public repo README: [`README.md`](../README.md)
- release operator guide: [`RELEASING.md`](../RELEASING.md)
- PyPI long description: [`docs/pypi.md`](pypi.md)
- Qwen validation evidence: [`docs/research/qwen35-validation-report.md`](research/qwen35-validation-report.md)
- brand system and launch kit: [`docs/brand/README.md`](brand/README.md)

Maintained-versus-experimental split:

- `blkbx_lab` plus the `blkbx-lab` CLI is the release surface that must stay documented and smoke-tested.
- `blkbxs`, `mand8`, `due`, and `mech_lab` are part of the shipped root wheel surface and must stay importable from a clean install.
- `blkbx_lab.research` and `blkbx_lab.experimental` stay opt-in helper namespaces whose dependency path is extras, not the default install.
- `products/*` remain source slices and should not be treated as separate published artifacts for the v0.9.1 local release gate.
