"""CLI entry points for hybrid-mechlab."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from hybrid_mechlab._version import __version__


def _cmd_from_mair(args: argparse.Namespace) -> int:
    from hybrid_mechlab.integrations.mair import load_trace_from_mair_manifest

    trace = load_trace_from_mair_manifest(args.manifest_path)
    record = trace.to_record()
    if args.output_path:
        target = Path(args.output_path)
        target.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
        print(target)
        return 0
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0


def _cmd_topology_offline(args: argparse.Namespace) -> int:
    from hybrid_mechlab.integrations.mair import load_trace_from_mair_manifest
    from hybrid_mechlab.topology.offline import export_mair_topology_artifacts

    trace = load_trace_from_mair_manifest(args.manifest_path)
    paths = export_mair_topology_artifacts(trace, args.out_dir)
    print(json.dumps(paths, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="hybrid-mechlab CLI")
    parser.add_argument("--version", action="store_true")
    subparsers = parser.add_subparsers(dest="command")

    from_mair = subparsers.add_parser("from-mair", help="Load a MAIR manifest and emit a hybrid-mechlab trace record")
    from_mair.add_argument("manifest_path")
    from_mair.add_argument("--output-path", default=None)
    from_mair.set_defaults(func=_cmd_from_mair)

    topology_offline = subparsers.add_parser(
        "topology-offline",
        help="Compute offline topology artifacts from a MAIR manifest",
    )
    topology_offline.add_argument("manifest_path")
    topology_offline.add_argument("--out-dir", required=True)
    topology_offline.set_defaults(func=_cmd_topology_offline)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        print(f"hybrid-mechlab {__version__}")
        return 0
    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return 0
    return int(func(args))


def from_mair_main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(["from-mair", *(argv or [])])
    return int(args.func(args))


def topology_offline_main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(["topology-offline", *(argv or [])])
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
