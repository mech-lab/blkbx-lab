#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCENARIO="${1:-lloyds_cyber_happy_path}"
OUTPUT_DIR="${MAND8_SMOKE_OUTPUT_DIR:-$ROOT/artifacts/mand8-lloyds-demo-smoke}"
MAND8_DIR="$OUTPUT_DIR/mand8"
INK_VECTOR_DIR="$OUTPUT_DIR/ink-vector"

cd "$ROOT/web/rails"
MAND8_SMOKE_SCENARIO="$SCENARIO" \
MAND8_SMOKE_OUTPUT_DIR="$MAND8_DIR" \
bundle exec rails runner script/mand8_lloyds_demo_smoke.rb

cd "$ROOT"
mkdir -p "$INK_VECTOR_DIR"

python3 - "$ROOT" "$INK_VECTOR_DIR" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
out_dir = pathlib.Path(sys.argv[2])
vector_catalog = json.loads((root / "test-vectors" / "ink-vectors.json").read_text(encoding="utf-8"))
vector = next(entry for entry in vector_catalog["vectors"] if entry["name"] == "valid_tlv_v2_trusted_manifest")

for filename, key in {
    "ink_receipt.v2.json": "receipt",
    "ink_manifest.v2.json": "manifest",
    "trust-registry.json": "trust_registry",
    "verify-policy.json": "verify_policy",
}.items():
    (out_dir / filename).write_text(json.dumps(vector[key], indent=2) + "\n", encoding="utf-8")
PY

cargo run --quiet -p ink-cli -- receipt \
  --receipt "$INK_VECTOR_DIR/ink_receipt.v2.json" \
  --manifest "$INK_VECTOR_DIR/ink_manifest.v2.json" \
  --trust-registry "$INK_VECTOR_DIR/trust-registry.json" \
  --policy "$INK_VECTOR_DIR/verify-policy.json" \
  > "$INK_VECTOR_DIR/ink-verification-report.json"

printf 'MAND8 workflow summary written to %s\n' "$MAND8_DIR/summary.json"
printf 'Native INK verifier report written to %s\n' "$INK_VECTOR_DIR/ink-verification-report.json"
printf 'Seeded MAND8 verifier handoff is expected to remain unavailable in v1 cleanup.\n'
printf 'Use %s to paste the INK vector files into /verify/index.html for browser parity checks.\n' "$INK_VECTOR_DIR"
