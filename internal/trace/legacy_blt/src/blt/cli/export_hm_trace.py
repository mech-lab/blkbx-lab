from __future__ import annotations

import argparse

from blt.export import export_hybrid_mechlab_trace


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Export a hybrid-mechlab-compatible trace from a MAIR manifest")
    parser.add_argument("manifest_path")
    parser.add_argument("--output-path", default=None)
    args = parser.parse_args(argv)
    path = export_hybrid_mechlab_trace(args.manifest_path, output_path=args.output_path)
    print(path)


if __name__ == "__main__":
    main()
