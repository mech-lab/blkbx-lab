#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if rg -n '\b(Vec|String|Box|BTreeMap|HashMap|alloc::)\b' rust/crates/ink-core/src \
  --glob '!tests.rs' \
  --glob '!legacy/**'; then
  echo "no-alloc check failed: heap-backed constructs found in ink-core/src"
  exit 1
fi

echo "ink-core no-alloc check passed"
