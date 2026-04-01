from __future__ import annotations

import argparse

from blt.export import run_analysis


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run BLT grouped CLT and intervention analysis")
    parser.add_argument("manifest_path")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args(argv)
    path = run_analysis(args.manifest_path, output_dir=args.output_dir)
    print(path)


if __name__ == "__main__":
    main()
