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
- `qwen35 deterministic demo`
- `local policy gate`

Avoid:

- `cutting-edge AI solution`
- `intuitive for anyone`
- `responsible AI future`
- `just plug in your model`

## Naming

- Use `BLKBX Lab` for the product.
- Use `mechlab-sdk` for install and published-package language.
- Use `blkbx-lab` for primary CLI examples.
- Use `blkbx_lab` for the primary Python namespace.
- Keep compatibility aliases and pre-BLKBX public names inside migration-specific material only.
- Do not use retired pre-BLKBX package names or install commands in release-facing materials.

## Visual Rules

- Ink and Chalk are the default structural colors.
- Teal carries verification and flow accents.
- Acid is the verification signal and should appear once per composition.
- Error red is reserved for failure or obstruction states.
- Use IBM Plex Mono for commands, code, metrics, labels, and terminal snippets.
- Keep SVG launch assets as the design source of truth, but use `assets/brand/og-card.png` for the live GitHub social preview setting.

## Release Notes

- Lead with what shipped.
- State the install package and primary CLI early.
- State CLI and API impact explicitly.
- State current limits without hedging.
