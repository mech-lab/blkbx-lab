from __future__ import annotations

import argparse
from pathlib import Path

from ._version import __version__
from .api import analyze, compare, demo, doctor, explain, gate, report, tamper, trace, verify


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="blkbx-lab CLI")
    parser.add_argument("--version", action="store_true")
    subparsers = parser.add_subparsers(dest="command")

    demo_parser = subparsers.add_parser("demo", help="Run the deterministic demo")
    demo_parser.add_argument("demo_name", nargs="?", default="qwen35")
    demo_parser.add_argument("--output-dir", default=None)
    demo_parser.set_defaults(func=_cmd_demo)

    doctor_parser = subparsers.add_parser("doctor", help="Check native runtime, trust policy, and signer state")
    doctor_parser.add_argument("--initialize-local-issuer", action="store_true")
    doctor_parser.set_defaults(func=_cmd_doctor)

    trace_parser = subparsers.add_parser("trace", help="Capture deterministic demo evidence")
    trace_parser.add_argument("prompt", nargs="?")
    trace_parser.add_argument("--prompt", dest="prompt_text", default=None)
    trace_parser.add_argument("--output-dir", default=None)
    trace_parser.add_argument("--trace-id", default=None)
    trace_parser.add_argument("--adapter", default="qwen35")
    trace_parser.add_argument("--backend", default=None)
    trace_parser.add_argument("--family", default=None)
    trace_parser.add_argument("--model", default=None)
    trace_parser.add_argument("--profile", default=None)
    trace_parser.set_defaults(func=_cmd_trace)

    analyze_parser = subparsers.add_parser("analyze", help="Validate a bundle and evaluate a policy")
    analyze_parser.add_argument("manifest_path")
    analyze_parser.add_argument("--policy", default=None)
    analyze_parser.add_argument("--controls", default=None)
    analyze_parser.add_argument("--output-dir", default=None)
    analyze_parser.add_argument("--profile", default=None)
    analyze_parser.set_defaults(func=_cmd_analyze)

    gate_parser = subparsers.add_parser("gate", help="Issue a signed v2 receipt")
    gate_parser.add_argument("manifest_path")
    gate_parser.add_argument("--policy", default=None)
    gate_parser.add_argument("--controls", default=None)
    gate_parser.add_argument("--output-path", default=None)
    gate_parser.add_argument("--profile", default=None)
    gate_parser.add_argument("--demo-signer", action="store_true")
    gate_parser.set_defaults(func=_cmd_gate)

    verify_parser = subparsers.add_parser("verify", help="Verify a receipt")
    verify_parser.add_argument("receipt_path")
    verify_parser.add_argument("--manifest-path", default=None)
    verify_parser.set_defaults(func=_cmd_verify)

    compare_parser = subparsers.add_parser("compare", help="Compare two verified v2 receipts")
    compare_parser.add_argument("--left", required=True)
    compare_parser.add_argument("--right", required=True)
    compare_parser.add_argument("--output-dir", default=None)
    compare_parser.set_defaults(func=_cmd_compare)

    tamper_parser = subparsers.add_parser("tamper", help="Mutate a receipt for demo purposes")
    tamper_parser.add_argument("receipt_path")
    tamper_parser.set_defaults(func=_cmd_tamper)

    explain_parser = subparsers.add_parser("explain", help="Explain the receipt decision")
    explain_parser.add_argument("receipt_path")
    explain_parser.set_defaults(func=_cmd_explain)

    report_parser = subparsers.add_parser("report", help="Render a human-readable summary")
    report_parser.add_argument("target")
    report_parser.add_argument("--kind", default=None)
    report_parser.set_defaults(func=_cmd_report)
    return parser


def _resolve_prompt(args: argparse.Namespace, parser: argparse.ArgumentParser) -> str:
    prompt = args.prompt_text or args.prompt
    if prompt is None:
        parser.error("trace requires a prompt via positional PROMPT or --prompt")
    return prompt


def _cmd_demo(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    result = demo(args.demo_name, output_dir=args.output_dir)
    print(result.report)
    print(f"Manifest: {result.manifest_path}")
    print(f"Receipt: {result.receipt_path}")
    return 0


def _cmd_doctor(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    result = doctor(initialize_local_issuer=args.initialize_local_issuer)
    print(result.report)
    return 0


def _cmd_trace(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    result = trace(
        _resolve_prompt(args, parser),
        output_dir=args.output_dir,
        trace_id=args.trace_id,
        adapter=args.adapter,
        backend=args.backend,
        family=args.family,
        model=args.model,
        profile=args.profile,
    )
    print(result.report)
    print(f"Manifest: {result.manifest_path}")
    return 0


def _cmd_analyze(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    result = analyze(
        args.manifest_path,
        policy=args.policy,
        controls=args.controls,
        output_dir=args.output_dir,
        profile=args.profile,
    )
    print(result.report)
    return 0 if result.recommended_decision == "pass" else 1


def _cmd_gate(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    result = gate(
        args.manifest_path,
        policy=args.policy,
        controls=args.controls,
        output_path=args.output_path,
        profile=args.profile,
        demo_signer=args.demo_signer,
    )
    print(result.report)
    return 0 if result.decision == "pass" else 1


def _cmd_verify(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    result = verify(args.receipt_path, manifest_path=args.manifest_path)
    print(result.report)
    return 0 if result.verification.get("overall") in {"pass", "legacy-valid"} else 1


def _cmd_compare(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    result = compare(left=args.left, right=args.right, output_dir=args.output_dir)
    print(result.report)
    print(f"Comparison packet: {result.comparison_path}")
    return 0


def _cmd_tamper(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    result = tamper(args.receipt_path)
    print(result.report)
    return 0


def _cmd_explain(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    print(explain(args.receipt_path))
    return 0


def _cmd_report(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    print(report(Path(args.target), kind=args.kind))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        print(f"blkbx-lab {__version__}")
        return 0
    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return 0
    return int(func(args, parser))


if __name__ == "__main__":
    raise SystemExit(main())
