import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_release_readiness_script_passes_without_clean_tree_enforcement():
    result = subprocess.run(
        [sys.executable, "scripts/check_release_readiness.py", "--skip-clean-worktree"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_local_release_script_passes_in_docs_only_mode():
    result = subprocess.run(
        [
            sys.executable,
            "scripts/check_local_release.py",
            "--skip-clean-worktree",
            "--skip-focused-tests",
            "--skip-ruff",
            "--skip-build",
            "--skip-smoke",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_qwen_report_scopes_workstation_paths_to_appendix():
    report = (ROOT / "docs" / "research" / "qwen35-validation-report.md").read_text(encoding="utf-8")
    marker = "## Reproducibility Appendix"
    assert marker in report
    main_body, appendix = report.split(marker, maxsplit=1)
    assert "/Volumes/" not in main_body
    assert "/Users/" not in main_body
    assert "/Volumes/" in appendix


def test_release_workflow_uses_authored_template():
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "body_path: .github/RELEASE_TEMPLATE.md" in workflow
    assert "generate_release_notes: true" not in workflow
    assert "assets/brand/og-card.png" in workflow
    assert "pypa/gh-action-pypi-publish@release/v1" in workflow
    assert "name: pypi" in workflow
    assert "id-token: write" in workflow
    assert "https://pypi.org/p/mechlab-sdk" in workflow


def test_host_ready_social_preview_asset_exists():
    assert (ROOT / "assets" / "brand" / "og-card.png").exists()


def test_bug_report_template_uses_published_package_name():
    template = (ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml").read_text(encoding="utf-8")
    assert "pip install --pre mechlab-sdk" in template
    assert "blkbx-lab" not in template
    assert "mechlab ..." not in template
