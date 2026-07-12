from __future__ import annotations

import argparse
import json
from typing import Any

from mair.hydrate import load_artifact_bundle, load_artifact_by_type


def _summarize_payload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, list):
        return {"kind": "rows", "count": len(payload)}
    if isinstance(payload, dict):
        return {"kind": "object", "keys": sorted(payload.keys())}
    return {"kind": type(payload).__name__}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Load validated artifacts from a MAIR manifest")
    parser.add_argument("manifest_path")
    parser.add_argument("--artifact-type", default=None)
    args = parser.parse_args(argv)

    if args.artifact_type:
        payload = load_artifact_by_type(args.manifest_path, args.artifact_type)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    bundle = load_artifact_bundle(args.manifest_path)
    summary = {
        "trace_id": bundle["manifest"]["trace_id"],
        "producer": bundle["manifest"]["producer"],
        "artifact_summaries": {
            artifact_type: _summarize_payload(payload)
            for artifact_type, payload in bundle["artifacts"].items()
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
