#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

check_no_alloc() {
  local crate_path="$1"
  shift
  if rg -n '\b(Vec|String|Box|BTreeMap|HashMap|alloc::)\b' "$crate_path" "$@"; then
    echo "no-alloc check failed: heap-backed constructs found in $crate_path"
    exit 1
  fi
}

check_no_alloc rust/crates/ink-core/src --glob '!tests.rs' --glob '!legacy/**'
check_no_alloc rust/crates/ink-verify/src

echo "ink-core and ink-verify no-alloc checks passed"
