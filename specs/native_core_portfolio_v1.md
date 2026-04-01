# Native Core Portfolio v1

## Portfolio lanes
- Native core:
  - `Gated DeltaNet`
  - `HGRN2`
  - `RetNet`
  - `Hawk`
  - `TransNormerLLM`
- Understanding first:
  - `Qwen3.5`
  - `OLMo Hybrid`
  - `Kimi Linear`
- Migration:
  - `Liger` through the `hm_liger` crate

## Contract rules
- `hm_core` owns the transport/topology substrate and stays `no_std`.
- `hm_liger` is a workspace-level migration layer and must not leak runtime-heavy dependencies into `hm_core`.
- `BLT/` consumes these contracts for replay/export and is not the source of truth for schedule or trace schemas.

## First milestone
- Prove the substrate with `Gated DeltaNet` as the first canonical native kernel.
- Keep `Qwen3.5` as the first real reference profile that every core abstraction must round-trip through.
- Use long-context reasoning as the first benchmark wedge and compare `native`, `adapter`, and `liger` traces with one schema.
