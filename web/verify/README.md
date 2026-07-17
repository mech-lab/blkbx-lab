# INK Static Verifier Scaffold

This directory is an in-repo static verifier scaffold that stays separate from the shipped native trust boundary.

## Current Scope

- `index.html`: static verifier shell
- `verify.js`: local structure-check placeholder until WASM wiring lands
- `styles.css`: standalone styling

## Boundary

The current public verification contract remains native and local through `blkbx-lab`, `ink`, and `ink-tui`.
