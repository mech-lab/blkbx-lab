# Sheaf / Connection v1

- Use partial sheaf abstractions to compare local sections across blocks, hook regions, and family-specific transport regimes.
- Support connection-like transport across block graphs and measure holonomy/loop defect independently of model family.
- Rust traits:
  - `PartialSection`
  - `RestrictionMap`
  - `PartialSheaf`
  - `DiscreteConnection`
- Family invariance rule:
  - `Gated DeltaNet`, `HGRN2`, `RetNet`, `Hawk`, `TransNormerLLM`, `Qwen3.5`, `OLMo Hybrid`, and `Kimi Linear` must all reuse the same sheaf/connection interfaces.
  - No family-specific topology or sheaf API is allowed in `hm_core`.
- Gluing defects remain first-class metrics for cross-block consistency and must be emitted against the same trace schema across `native`, `adapter`, and `liger` backends.
