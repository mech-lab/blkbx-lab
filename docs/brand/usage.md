# Engineer Usage Note

Use this when editing release-facing docs, release notes, launch cards, or repo metadata.

## Voice

- Name things exactly.
- State the public contract directly.
- Explain limits concretely.
- Do not use hype, hedging, or value-signaling filler.

Preferred phrasing:

- `Ink Receipt`
- `Action Evidence Bundle`
- `Receipt`
- `Comparison Packet`
- `Qwen3.5 claims demo`
- `local policy gate`

Avoid:

- `cutting-edge AI solution`
- `intuitive for anyone`
- `responsible AI future`
- `just plug in your model`

## Naming

- Use `BLKBX Lab` for the product.
- Use `blkbx-lab` for the published package and CLI.
- Use `blkbx_lab` for the Python namespace.
- Keep deprecated pre-BLKBX public names inside migration-specific material only.
- Do not use `HybridTDA`, `hybridtda`, or `pip install hybridtda` in release-facing materials.

## Visual Rules

- Ink and Chalk are the default structural colors.
- Teal carries verification and flow accents.
- Acid is the verification signal and should appear once per composition.
- Error red is reserved for failure or obstruction states.
- Use IBM Plex Mono for commands, code, metrics, labels, and terminal snippets.
- Keep SVG launch assets as the design source of truth, but use `assets/brand/og-card.png` for the live GitHub social preview setting.

## Release Notes

- Lead with what shipped.
- State the public contract early.
- State CLI and API impact explicitly.
- State current limits without hedging.
