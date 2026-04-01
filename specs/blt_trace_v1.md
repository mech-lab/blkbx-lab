# BLT Trace v1

- Block-Level Transcoder (BLT) captures sparse codes and transport summaries per block.
- Trace contents: prompt metadata, schedule id, hook captures, sparse codes, signed sketches, interventions, reproducibility manifest.
- Primary outputs: sparse codes, transport digests, topology sketches, replacement-mode metrics, attribution exports.
- Replacement-mode ready: traces must support replay with sparse-code substitution.
