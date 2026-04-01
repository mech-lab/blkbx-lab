from __future__ import annotations

import argparse
import json

from mair.gates import write_receipt


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run MAIR assurance gates against a manifest")
    parser.add_argument("manifest_path")
    parser.add_argument("--profile", default=None, help="Path to a JSON gate profile")
    parser.add_argument("--output-path", default=None)
    args = parser.parse_args(argv)

    profile = None
    if args.profile is not None:
        with open(args.profile, "r", encoding="utf-8") as handle:
            profile = json.load(handle)

    path = write_receipt(args.manifest_path, profile=profile, output_path=args.output_path)
    print(path)
