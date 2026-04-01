from __future__ import annotations

import argparse

from blt.export import run_trace


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Materialize MAIR artifacts from a BLT trace")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--trace-id", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--backend", default="mock", choices=["mock", "qwen_hybrid_hf"])
    parser.add_argument("--profile", default=None)
    parser.add_argument("--model-family", default=None)
    parser.add_argument("--model-variant", default=None)
    args = parser.parse_args(argv)
    path = run_trace(
        prompt=args.prompt,
        trace_id=args.trace_id,
        output_dir=args.out_dir,
        backend=args.backend,
        profile=args.profile,
        model_family=args.model_family,
        model_variant=args.model_variant,
    )
    print(path)


if __name__ == "__main__":
    main()
