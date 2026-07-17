#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOCUSED_RELEASE_TESTS = (
    "tests/test_brand_release_assets.py",
    "tests/test_packaging_contracts.py",
    "tests/test_readme_example.py",
    "tests/test_release_readiness.py",
    "tests/test_mech_lab_product.py",
    "tests/test_mech_lab_doctor.py",
    "tests/test_umbrella_product_imports.py",
    "tests/test_version_sync.py",
)

def _check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)

def _run(args: list[str], *, cwd: Path = ROOT) -> None:
    subprocess.run(args, cwd=cwd, check=True)

def current_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', text, re.MULTILINE)
    _check(match is not None, "could not determine project version from pyproject.toml")
    return str(match.group(1))

def ensure_clean_worktree() -> None:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    _check(not result.stdout.strip(), "git worktree is not clean")

def run_release_readiness(skip_clean_worktree: bool) -> None:
    args = [sys.executable, "scripts/check_release_readiness.py"]
    if skip_clean_worktree:
        args.append("--skip-clean-worktree")
    _run(args)

def run_focused_release_tests() -> None:
    _run([sys.executable, "-m", "pytest", "-q", *FOCUSED_RELEASE_TESTS])

def run_ruff() -> None:
    _run([sys.executable, "-m", "ruff", "check", "."])

def clean_artifacts() -> None:
    """Remove stale dist/, build/, and wheel outputs before building."""
    for pattern in ["dist", "build", "*.egg-info"]:
        for path in ROOT.glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink(missing_ok=True)
    for path in (ROOT / "target" / "wheels", ROOT / "target" / "maturin"):
        if path.exists():
            shutil.rmtree(path)

def built_artifacts(version: str) -> tuple[Path, Path]:
    dist_dir = ROOT / "dist"
    wheels = sorted(dist_dir.glob(f"*{version}*.whl"))
    sdists = sorted(dist_dir.glob(f"*{version}*.tar.gz"))
    _check(len(wheels) == 1, f"expected exactly one wheel for {version}, found {len(wheels)}")
    _check(len(sdists) == 1, f"expected exactly one sdist for {version}, found {len(sdists)}")
    other_artifacts = [
        path for path in dist_dir.iterdir()
        if path not in {wheels[0], sdists[0]}
    ]
    _check(not other_artifacts, f"dist contains unexpected extra artifacts: {[path.name for path in other_artifacts]}")
    return wheels[0], sdists[0]

def build_and_validate() -> None:
    """Build the current version and validate artifacts."""
    version = current_version()
    _run([sys.executable, "-m", "build"])
    wheel, sdist = built_artifacts(version)
    _run([sys.executable, "-m", "twine", "check", str(wheel), str(sdist)])

def _venv_paths(venv_path: Path) -> tuple[Path, Path, Path, Path]:
    if sys.platform == "win32":
        pip_path = venv_path / "Scripts" / "pip"
        python_path = venv_path / "Scripts" / "python"
        cli_path = venv_path / "Scripts" / "blkbx-lab"
        mechlab_cli_path = venv_path / "Scripts" / "mechlab"
    else:
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"
        cli_path = venv_path / "bin" / "blkbx-lab"
        mechlab_cli_path = venv_path / "bin" / "mechlab"
    return pip_path, python_path, cli_path, mechlab_cli_path


def _run_python(python_path: Path, source: str) -> None:
    result = subprocess.run(
        [str(python_path), "-c", source],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    _check(result.returncode == 0, result.stderr or result.stdout)


def _run_cli(command: list[str]) -> None:
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    _check(result.returncode == 0, result.stderr or result.stdout)

def run_smoke_tests() -> None:
    """Run fresh-venv wheel and sdist smoke tests."""
    version = current_version()
    wheel, sdist = built_artifacts(version)

    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / "venv"
        _run([sys.executable, "-m", "venv", str(venv_path)], cwd=ROOT)
        pip_path, python_path, cli_path, mechlab_cli_path = _venv_paths(venv_path)
        _run([str(pip_path), "install", "--upgrade", "pip"], cwd=ROOT)
        _run([str(pip_path), "install", str(wheel)], cwd=ROOT)
        _run_python(
            python_path,
            """
import blkbx_lab as bl
import blkbx_lab.artifacts as artifact_resources
import blkbx_lab.evidence as evidence_resources
import blkbxs
import due
import mand8
import mech_lab as ml

result = bl.demo(output_dir="artifacts/wheel-smoke")
print(result.manifest_path)
print(result.receipt_path)
print(bl.verify(result.receipt_path).report)
print(blkbxs.doctor().report)
print(mand8.receipt.create()["schema"])
print(due.receipt.create()["schema"])
print(evidence_resources.load_schema("ink.evidence.record.v1")["$id"])
print(artifact_resources.load_schema("ink.export_manifest.v1")["$id"])
print(ml.research.describe()["extra"])
""",
        )
        _run_cli([str(cli_path), "doctor"])
        _run_cli([str(mechlab_cli_path), "doctor"])

    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / "venv"
        _run([sys.executable, "-m", "venv", str(venv_path)], cwd=ROOT)
        pip_path, python_path, cli_path, mechlab_cli_path = _venv_paths(venv_path)
        _run([str(pip_path), "install", "--upgrade", "pip"], cwd=ROOT)
        _run([str(pip_path), "install", str(sdist)], cwd=ROOT)
        _run_python(
            python_path,
            """
import blkbx_lab as bl
import blkbx_lab.artifacts as artifact_resources
import blkbx_lab.evidence as evidence_resources
import blkbxs
import due
import mand8
import mech_lab as ml

result = bl.demo(output_dir="artifacts/sdist-smoke")
print(result.manifest_path)
print(result.receipt_path)
print(bl.verify(result.receipt_path).report)
print(blkbxs.doctor().report)
print(mand8.receipt.create()["schema"])
print(due.receipt.create()["schema"])
print(evidence_resources.load_schema("ink.evidence.record.v1")["$id"])
print(artifact_resources.load_schema("ink.export_manifest.v1")["$id"])
print(ml.experimental.describe()["extra"])
""",
        )
        _run_cli([str(cli_path), "doctor"])
        _run_cli([str(mechlab_cli_path), "doctor"])

    for extra_name, expected_module in (
        ("research", "markdown_it"),
        ("experimental", "rich"),
        ("all", "rich"),
    ):
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "venv"
            _run([sys.executable, "-m", "venv", str(venv_path)], cwd=ROOT)
            pip_path, python_path, _, _ = _venv_paths(venv_path)
            _run([str(pip_path), "install", "--upgrade", "pip"], cwd=ROOT)
            _run(
                [str(pip_path), "install", "--find-links", "dist", f"mechlab-sdk[{extra_name}]=={version}"],
                cwd=ROOT,
            )
            _run_python(
                python_path,
                f"""
import importlib.util
import blkbx_lab as bl

assert importlib.util.find_spec("{expected_module}") is not None
print(bl.research.describe()["extra"])
print(bl.experimental.describe()["extra"])
""",
            )

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate local release readiness for the root mechlab-sdk release surface.")
    parser.add_argument(
        "--skip-clean-worktree",
        action="store_true",
        help="Skip the clean git worktree check. Use only for local in-progress validation.",
    )
    parser.add_argument(
        "--skip-ruff",
        action="store_true",
        help="Skip the repo-root ruff check.",
    )
    parser.add_argument(
        "--skip-focused-tests",
        action="store_true",
        help="Skip the focused public-contract release test suite.",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip building and validating versioned artifacts.",
    )
    parser.add_argument(
        "--skip-smoke",
        action="store_true",
        help="Skip smoke tests.",
    )
    args = parser.parse_args(argv)

    if not args.skip_clean_worktree:
        ensure_clean_worktree()

    run_release_readiness(skip_clean_worktree=args.skip_clean_worktree)
    print("release readiness checks passed")

    if not args.skip_ruff:
        run_ruff()
        print("ruff checks passed")

    if not args.skip_focused_tests:
        run_focused_release_tests()
        print("focused release tests passed")

    if not args.skip_build:
        clean_artifacts()
        build_and_validate()
        print("build and artifact validation passed")

    if not args.skip_smoke:
        run_smoke_tests()
        print("smoke tests passed")

    print("local release readiness check completed successfully")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
