# Sparse Codes v1

- Sparse-first representation for block-level activations.
- Fixed-capacity sparse vectors and ragged batches in Rust `hm_core::sparse`.
- Python side exposes `SparseCodeBatch` for encoders/decoders and exporters.
- Must be deterministic and hashable for audit.
