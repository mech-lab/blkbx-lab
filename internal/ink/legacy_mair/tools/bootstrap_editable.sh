#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd "$script_dir/../../.." && pwd)

python -m pip install -e "$repo_root/internal/ink/legacy_mair[dev]" -e "$repo_root/internal/trace/legacy_blt[dev]"
