from __future__ import annotations

import argparse

from hybrid_mechlab._version import __version__
from mech_lab.api import analyze, compare, demo, doctor, explain, gate, report, trace


def _resolve_prompt(args: argparse.Namespace, parser: argparse.ArgumentParser) -> str:
    prompt = args.prompt_text or args.prompt
    if prompt is None:
        parser.error("trace requires a prompt via positional PROMPT or --prompt")
    return prompt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="mech-lab CLI")
    parser.add_argument("--version", action="store_true")
    subparsers = parser.add_subparsers(dest="command")

    demo_parser = subparsers.add_parser("demo", help="Generate a deterministic evidence bundle and receipt")
    demo_parser.add_argument("--output-dir", default=None)
    demo_parser.add_argument("--trace-id", default=None)
    demo_parser.add_argument("--prompt", dest="prompt_text", default=None)
    demo_parser.set_defaults(func=_cmd_demo)

    doctor_parser = subparsers.add_parser("doctor", help="Check local mech-lab readiness")
    doctor_parser.set_defaults(func=_cmd_doctor)

    trace_parser = subparsers.add_parser("trace", help="Capture a trace and emit a portable evidence bundle")
    trace_parser.add_argument("prompt", nargs="?")
    trace_parser.add_argument("--prompt", dest="prompt_text", default=None)
    trace_parser.add_argument("--output-dir", default=None)
    trace_parser.add_argument("--trace-id", default=None)
    trace_parser.add_argument("--backend", default=None)
    trace_parser.add_argument("--family", default=None)
    trace_parser.add_argument("--model", default=None)
    trace_parser.add_argument("--profile", default=None)
    trace_parser.set_defaults(func=_cmd_trace)

    analyze_parser = subparsers.add_parser("analyze", help="Run grouped CLT and topology analysis for one bundle")
    analyze_parser.add_argument("manifest_path")
    analyze_parser.add_argument("--output-dir", default=None)
    analyze_parser.add_argument("--profile", default=None)
    analyze_parser.set_defaults(func=_cmd_analyze)

    compare_parser = subparsers.add_parser("compare", help="Emit a MAIR-backed comparison packet from two bundles")
    compare_parser.add_argument("--left", required=True)
    compare_parser.add_argument("--right", required=True)
    compare_parser.add_argument("--output-dir", default=None)
    compare_parser.set_defaults(func=_cmd_compare)

    gate_parser = subparsers.add_parser("gate", help="Evaluate release gates and emit a receipt")
    gate_parser.add_argument("manifest_path")
    gate_parser.add_argument("--policy", default="release-assurance")
    gate_parser.add_argument("--profile", default=None)
    gate_parser.add_argument("--output-path", default=None)
    gate_parser.set_defaults(func=_cmd_gate)

    explain_parser = subparsers.add_parser("explain", help="Explain a receipt in plain language")
    explain_parser.add_argument("receipt_path")
    explain_parser.set_defaults(func=_cmd_explain)

    report_parser = subparsers.add_parser("report", help="Render a human-readable report")
    report_parser.add_argument("target")
    report_parser.add_argument("--kind", default=None)
    report_parser.set_defaults(func=_cmd_report)
    return parser


def _cmd_demo(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    result = demo(output_dir=args.output_dir, trace_id=args.trace_id, prompt=args.prompt_text or "Produce a deterministic mechanistic evidence bundle for a hybrid trace.")
    print(result.report)
    print("")
    print(f"Manifest: {result.manifest_path}")
    if result.receipt_path:
        print(f"Receipt: {result.receipt_path}")
    return 0


def _cmd_doctor(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    result = doctor()
    print(result.report)
    return 0 if result.demo_ready else 1


def _cmd_trace(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    result = trace(
        _resolve_prompt(args, parser),
        output_dir=args.output_dir,
        trace_id=args.trace_id,
        backend=args.backend,
        family=args.family,
        model=args.model,
        profile=args.profile,
    )
    print(result.report)
    print("")
    print(f"Manifest: {result.manifest_path}")
    return 0


def _cmd_analyze(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    result = analyze(args.manifest_path, output_dir=args.output_dir, profile=args.profile)
    print(result.report)
    return 0


def _cmd_compare(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    result = compare(left=args.left, right=args.right, output_dir=args.output_dir)
    print(result.report)
    print("")
    print(f"Comparison packet: {result.comparison_path}")
    return 0


def _cmd_gate(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    result = gate(args.manifest_path, policy=args.policy, profile=args.profile, output_path=args.output_path)
    print(result.report)
    return 0 if result.decision == "pass" else 1


def _cmd_explain(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    print(explain(args.receipt_path))
    return 0


def _cmd_report(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    print(report(args.target, kind=args.kind))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        print(f"mech-lab {__version__}")
        return 0
    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return 0
    return int(func(args, parser))


if __name__ == "__main__":
    raise SystemExit(main())
