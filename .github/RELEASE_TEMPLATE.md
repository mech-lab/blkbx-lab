<!-- Drafted automatically from the authored template. Replace bracketed text before publishing. -->

> Open-source Ink Receipt gates for accountable AI agents.
>
> `qwen35` is the installed deterministic demo. Receipt gates are the standard.

## What Shipped

- [One sentence on the release intent.]
- [One sentence on the user-visible result.]

## Public Contract

- [List package, CLI, API, or artifact changes.]
- [Say `No public contract change.` when nothing changed.]
- [If product APIs changed, call out `blkbxs`, `mand8`, `due`, or extras explicitly.]

## qwen35 Demo Status

- [State whether this release changes the installed Qwen3.5 demo path.]
- [Link the validation report when that path changed materially.]
- [State any current limit explicitly.]

## Artifact Contract

- [Summarize any Ink manifest, receipt, or comparison packet impact.]
- [Say `No Ink artifact contract change.` when nothing changed.]

## Install

```bash
pip install mechlab-sdk==<version>
blkbx-lab demo qwen35 --output-dir artifacts/release-demo
python -c "import blkbxs, mand8, due"
```

## Known Limits

- [List concrete limits only.]
- [Avoid hype, hedging, or value-signaling language.]
