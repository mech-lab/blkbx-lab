from __future__ import annotations

import argparse

from mair.manifest import write_manifest


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Write a MAIR manifest for a run directory")
    parser.add_argument("run_dir")
    parser.add_argument("trace_id")
    parser.add_argument("--producer", default="mair:cli:0.1.0")
    args = parser.parse_args(argv)
    path = write_manifest(args.run_dir, trace_id=args.trace_id, producer=args.producer)
    print(path)


if __name__ == "__main__":
    main()
