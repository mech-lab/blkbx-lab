import json
from struct import unpack
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_brand_tokens_match_release_palette():
    palette = json.loads((ROOT / "assets" / "brand" / "palette.json").read_text(encoding="utf-8"))
    assert palette["ink"]["primary"] == "#0A0A0A"
    assert palette["ink"]["accent"] == "#00E5A0"
    assert palette["paper"]["base"] == "#FFFFFF"
    assert palette["paper"]["muted"] == "#F5F5F5"
    assert palette["signal"]["pass"] == "#00E5A0"
    assert palette["signal"]["fail"] == "#FF3B30"
    assert palette["signal"]["warn"] == "#FF9F0A"


def test_brand_css_implements_core_tokens():
    css = (ROOT / "assets" / "brand" / "tokens.css").read_text(encoding="utf-8")
    assert "--ink-primary: #0A0A0A;" in css
    assert "--ink-accent: #00E5A0;" in css
    assert "--paper-base: #FFFFFF;" in css
    assert "--paper-muted: #F5F5F5;" in css
    assert "--signal-pass: #00E5A0;" in css
    assert "--signal-fail: #FF3B30;" in css
    assert "--signal-warn: #FF9F0A;" in css


def test_launch_asset_kit_exists():
    kit = ROOT / "assets" / "brand" / "launch-kit"
    assert (kit / "og-card.png").exists()
    assert (kit / "og-card@2x.png").exists()
    assert (kit / "favicon.ico").exists()
    assert (kit / "apple-touch-icon.png").exists()


def test_host_ready_preview_export_has_expected_dimensions():
    preview = ROOT / "assets" / "brand" / "host-ready-preview.png"
    assert preview.exists()
    with preview.open("rb") as handle:
        header = handle.read(24)
    assert header.startswith(b"\x89PNG\r\n\x1a\n")
    assert unpack(">II", header[16:24]) == (1200, 630)


def test_public_release_surfaces_use_current_brand_names():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "BLKBX Lab" in readme
    assert "INK Receipts" in readme
    assert "Black Box Labs" in readme
    assert "MAND8" in readme
    assert "DUE" in readme


def test_readme_and_release_template_use_brand_lines():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    template = (ROOT / ".github" / "RELEASE_TEMPLATE.md").read_text(encoding="utf-8")
    assert "Open-source Ink Receipt gates for accountable AI agents." in readme
    assert "`qwen35` is the installed deterministic demo. Receipt gates are the standard." in readme
    assert "Open-source Ink Receipt gates for accountable AI agents." in template
    assert "`qwen35` is the installed deterministic demo. Receipt gates are the standard." in template


def test_release_workflow_uploads_host_ready_preview_asset():
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "assets/brand/og-card.png" in workflow
