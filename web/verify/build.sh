#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET_DIR="$ROOT/target/wasm32-unknown-unknown/release"
OUT_DIR="$ROOT/web/verify/pkg"

cd "$ROOT"

cargo build --release --target wasm32-unknown-unknown -p ink-wasm
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"
wasm-bindgen \
  --target web \
  --out-dir "$OUT_DIR" \
  --out-name ink_wasm \
  "$TARGET_DIR/ink_wasm.wasm"

printf 'Built web verifier package in %s\n' "$OUT_DIR"
