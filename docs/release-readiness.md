# Release Readiness Checklist

Current alpha verdict:

- the public BLKBX Lab contract is centered on `blkbx-lab` / `blkbx_lab`
- remaining release risk is mostly documentation, packaging, and operator discipline
- deprecated shim paths should remain migration-only and out of release-facing copy

Automated gates:

- `python scripts/check_release_readiness.py`
- focused public-contract test suite
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
- confirm the PyPI pending publisher is configured for `blkbx-lab / mech-lab / blkbx-lab / release.yml / pypi`

Current source-of-truth docs:

- public repo README: [`README.md`](../README.md)
- release operator guide: [`RELEASING.md`](../RELEASING.md)
- PyPI long description: [`docs/pypi.md`](pypi.md)
- Qwen validation evidence: [`docs/research/qwen35-validation-report.md`](research/qwen35-validation-report.md)
- brand system and launch kit: [`docs/brand/README.md`](brand/README.md)
