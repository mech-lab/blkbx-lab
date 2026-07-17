from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CRATE_CARGOS = [
    ROOT / "rust" / "crates" / "ink-receipt-v2" / "Cargo.toml",
    ROOT / "rust" / "crates" / "ink-cli" / "Cargo.toml",
    ROOT / "rust" / "crates" / "ink-tui" / "Cargo.toml",
]

BANNED_NETWORK_DEPS = {
    "reqwest",
    "hyper",
    "ureq",
    "surf",
    "tungstenite",
    "tokio-tungstenite",
    "websocket",
    "awc",
}


def test_zero_js_native_verifier_crates_do_not_pull_network_clients() -> None:
    for cargo_toml in CRATE_CARGOS:
        text = cargo_toml.read_text(encoding="utf-8")
        for dep in BANNED_NETWORK_DEPS:
            assert dep not in text, f"{dep} unexpectedly present in {cargo_toml}"
