import json
from struct import unpack
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "docs" / "brand"
ASSETS = ROOT / "assets" / "brand"


def test_brand_tokens_match_release_palette():
    data = json.loads((BRAND / "tokens.json").read_text(encoding="utf-8"))
    assert data["color"] == {
        "ink": "#0D0F0E",
        "chalk": "#F0EDE6",
        "slate": "#6B7068",
        "acid": "#B8FF57",
        "deep_teal": "#1C6B5A",
        "error_red": "#C73A2A",
    }
    assert data["copy"]["short_tagline"] == "Mechanistic interpretability that ships."
    assert "HybridTDA" in data["rules"]["forbidden_release_terms"]


def test_brand_css_implements_core_tokens():
    css = (BRAND / "tokens.css").read_text(encoding="utf-8")
    for value in ("#0d0f0e", "#f0ede6", "#6b7068", "#b8ff57", "#1c6b5a", "#c73a2a"):
        assert value in css
    assert "DM Serif Display" in css
    assert "IBM Plex Sans" in css
    assert "IBM Plex Mono" in css


def test_launch_asset_kit_exists():
    expected = (
        ASSETS / "og-card.png",
        ASSETS / "og-card.svg",
        ASSETS / "launch-card.svg",
        ASSETS / "release-header.svg",
        ASSETS / "logo-mark.svg",
        ASSETS / "badges" / "tier-a.svg",
        ASSETS / "badges" / "slsa-l3.svg",
        ASSETS / "badges" / "verified.svg",
        ASSETS / "badges" / "mair-ir-v1.svg",
        ASSETS / "icons" / "receipt.svg",
        ASSETS / "icons" / "mair-ir.svg",
        ASSETS / "icons" / "holonomy.svg",
        ASSETS / "icons" / "obstruction.svg",
        ASSETS / "icons" / "tier-a.svg",
    )
    for path in expected:
        assert path.exists(), path


def test_host_ready_preview_export_has_expected_dimensions():
    with (ASSETS / "og-card.png").open("rb") as handle:
        header = handle.read(24)
    assert header.startswith(b"\x89PNG\r\n\x1a\n")
    assert unpack(">II", header[16:24]) == (1280, 640)


def test_public_release_surfaces_use_current_brand_names():
    checked_files = (
        ROOT / "README.md",
        ROOT / "RELEASING.md",
        ROOT / "docs" / "pypi.md",
        ROOT / "docs" / "qwen35-validation-report.md",
        ROOT / "docs" / "release-readiness.md",
        ROOT / ".github" / "RELEASE_TEMPLATE.md",
    )
    forbidden = ("HybridTDA", "hybridtda", "pip install hybridtda")
    for path in checked_files:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{token} present in {path}"


def test_readme_and_release_template_use_brand_lines():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    template = (ROOT / ".github" / "RELEASE_TEMPLATE.md").read_text(encoding="utf-8")
    assert "Mechanistic interpretability that ships." in readme
    assert "Architecture-agnostic IR" in readme
    assert "Mechanistic interpretability that ships." in template
    assert "Real Model Proof" in template


def test_release_workflow_uploads_host_ready_preview_asset():
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "assets/brand/og-card.png" in workflow
