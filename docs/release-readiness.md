# Release Readiness Checklist

Current alpha verdict:

- the public BLKBX Lab contract is centered on `blkbx-lab` / `blkbx_lab`
- remaining release risk is mostly packaging discipline, signer configuration clarity, and test coverage
- release-facing copy must describe only the shipped product repo, not removed research trees

Automated gates:

- `python scripts/check_release_readiness.py`
- `python -m ruff check .`
- `python -m pyright`
- focused public-contract test suite
- `python -m pytest -q`
- `python3 -m build`
- `python3 -m twine check dist/*`
- fresh-venv wheel and sdist smoke installs

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
- confirm the PyPI pending publisher is configured for `blkbx-lab / blkbx-lab / .github/workflows/release.yml / pypi`

Current source-of-truth docs:

- public repo README: [`README.md`](../README.md)
- release operator guide: [`RELEASING.md`](../RELEASING.md)
- PyPI long description: [`docs/pypi.md`](pypi.md)
- Qwen validation evidence: [`docs/research/qwen35-validation-report.md`](research/qwen35-validation-report.md)
- brand system and launch kit: [`docs/brand/README.md`](brand/README.md)

Maintained-versus-experimental split:

- `blkbx_lab` plus the `blkbx-lab` CLI is the release surface that must stay documented and smoke-tested.
- `python/blkbx_lab`, `rust/crates/ink-core`, `rust/crates/ink-host`, `rust/crates/ink-py`, `policies`, and `schemas` are the only source trees that should influence the shipped `pip install blkbx-lab` surface.
