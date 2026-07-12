# Qwen3.5 Tract/Bridge Interpretation

This document preserves the advanced mechanistic interpretability module for Qwen3.5, focusing on the tract/bridge architecture.

## Overview

The Qwen3.5 architecture can be analyzed using a tract/bridge model, where:
- **Tracts** represent local, specialized processing units.
- **Bridges** represent global communication pathways between tracts.

## Metrics

The following metrics are available as optional evidence enrichments:

- **Bridge Dependence:** Measures how much a tract relies on information from other tracts via bridges.
- **Tract vs Bridge Report:** A detailed breakdown of computation distribution between tracts and bridges.
- **Compression-Forgetting Report:** Analyzes information loss during compression within tracts.
- **Hook Validation:** Ensures that the necessary hooks are present for accurate tract/bridge analysis.

## Usage

These metrics are not required for the core BLKBX Lab SDK functionality. They are intended for advanced users who need deeper insights into model behavior.
