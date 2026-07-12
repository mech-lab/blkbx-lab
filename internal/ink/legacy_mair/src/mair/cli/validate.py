from __future__ import annotations

import argparse
from pathlib import Path

from mair.validate import validate_artifact, validate_manifest


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Validate a MAIR artifact or manifest")
    parser.add_argument("path", help="Artifact or manifest path")
    parser.add_argument("--artifact-type", default=None)
    args = parser.parse_args(argv)
    path = Path(args.path)
    if path.name == "mair_manifest.v1.json":
        validate_manifest(path)
    else:
        validate_artifact(path, artifact_type=args.artifact_type)
    print(f"validated {path}")


if __name__ == "__main__":
    main()
