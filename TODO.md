# BLKBX Lab TODO

Repository: `https://github.com/mech-lab/blkbx-lab.git`

Clone status from this runtime: attempted `git clone`, but the container could not resolve `github.com`. Repo inspection below is based on the GitHub connector and the current public files.

## P0 — make the rebrand internally consistent

- [ ] Update `docs/pypi.md` from old `mech-lab` / `mechlab-sdk` / `mechlab` copy to `BLKBX Lab` / `blkbx-lab` / `blkbx_lab`.
- [ ] Update `docs/mvp-cli-api-contract.md` so the release-facing identity is `blkbx-lab`, not `mech-lab`.
- [ ] Update `docs/developer-architecture.md` so `blkbx_lab/` and `blkbx-lab` are the public SDK and CLI.
- [ ] Keep `mech_lab` and `mechlab` only as deprecated compatibility shims, with warnings.
- [ ] Replace old artifact names in docs where public-facing: `mair_manifest.v1.json` → `ink_manifest.v1.json`; `assurance_receipt.v1.json` → `ink_receipt.v1.json`; `backend_comparison.v1.json` → `receipt_comparison.v1.json`.

## P0 — fix public package metadata

- [ ] Replace old `pyproject.toml` keywords: `mechanistic-interpretability`, `holonomy`, `mair`, `research`, `slsa`.
- [ ] Add BLKBX Lab keywords: `accountable-ai`, `ai-agents`, `ink-receipts`, `receipt-gates`, `qwen35`, `gated-deltanet`, `hybrid-ai`, `insurtech`.
- [ ] Change package audience classifier away from pure `Science/Research` toward developers / software engineering.
- [ ] Change author metadata from `mech-lab team` to `BLKBX Lab contributors` or `Bankabil / BLKBX Lab contributors`.
- [ ] Decide final homepage URL: `https://blkbx.bankabil.com/lab` or current GitHub URL.

## P0 — replace mock evidence with real hashes

- [ ] Remove every public `sha256:mock` from generated artifacts.
- [ ] Add canonical helpers:
  - [ ] `hash_bytes(data: bytes) -> str`
  - [ ] `hash_text(text: str) -> str`
  - [ ] `hash_file(path: Path) -> str`
  - [ ] `canonical_json_hash(obj: dict) -> str`
- [ ] Hash `action.json` after writing.
- [ ] Hash prompt text and include it in the manifest.
- [ ] Hash demo claim and policy fixtures.
- [ ] Hash tool-call outputs, even when fixture-backed.
- [ ] Add tests proving hash changes when action, evidence, or policy fields change.

## P0 — make signing honest

- [ ] Audit current `internal/ink/signing.py` and `internal/ink/verify.py`.
- [ ] If the current mode is dev/mock signing, rename algorithm labels accordingly: `dev-hmac-sha512` or `dev-signature`, not `ed25519`.
- [ ] Add real Ed25519 signing via `cryptography` or `pynacl`.
- [ ] Keep dev signing behind explicit `--dev-key` or `BLKBX_LAB_DEV_SIGNING=1`.
- [ ] Verify should distinguish:
  - [ ] schema validity
  - [ ] canonical hash validity
  - [ ] signature validity
  - [ ] unsupported algorithm
  - [ ] key mismatch
  - [ ] tampered payload

## P0 — make `verify` actually prove tamper failure

- [ ] Add golden receipt fixture that verifies clean.
- [ ] Add tampered fixture with changed `gate.decision` that must fail.
- [ ] Add tampered fixture with changed `action.type` that must fail.
- [ ] Add tampered fixture with changed `evidence.input_hashes` that must fail.
- [ ] Add CLI tests:
  - [ ] `blkbx-lab verify clean.json` exits `0`.
  - [ ] `blkbx-lab verify tampered.json` exits nonzero.
  - [ ] `blkbx-lab tamper clean.json && blkbx-lab verify ink_receipt.tampered.json` fails.

## P1 — implement the actual thin-waist adapter contract

- [ ] Create `adapters/base.py` with `ModelAdapter` protocol.
- [ ] Required adapter methods:
  - [ ] `model_info() -> dict`
  - [ ] `architecture_profile() -> dict`
  - [ ] `propose_action(task: str, context: list[EvidenceRef]) -> ActionProposal`
  - [ ] `run(prompt: str, context: list[EvidenceRef] | None = None) -> ModelRunResult`
- [ ] Add adapter registry:
  - [ ] `register_adapter(name, adapter_cls)`
  - [ ] `get_adapter(name)`
- [ ] Make CLI options actually route:
  - [ ] `--backend`
  - [ ] `--family`
  - [ ] `--model`
  - [ ] `--profile`
- [ ] Keep `qwen35` as the installed default, not the hardcoded only path.

## P1 — improve Qwen3.5 claims demo

- [ ] Add real demo fixture files:
  - [ ] `examples/qwen35_claims/claim_001.md`
  - [ ] `examples/qwen35_claims/policy_001.md`
  - [ ] `examples/qwen35_claims/mandate_001.json`
  - [ ] `examples/qwen35_claims/gate_policy.yaml`
- [ ] Make the demo action derive from fixture context instead of a fully hardcoded action.
- [ ] Emit a full bundle directory:
  - [ ] `ink_manifest.v1.json`
  - [ ] `action.json`
  - [ ] `evidence/*.sha256`
  - [ ] `gate_decision.v1.json`
  - [ ] `ink_receipt.v1.json`
  - [ ] `report.md`
- [ ] Ensure `blkbx-lab demo qwen35-claims` prints the teaching story clearly:
  - [ ] model identity captured
  - [ ] mandate present
  - [ ] evidence hashes created
  - [ ] policy reference attached
  - [ ] customer impact detected
  - [ ] human review required
  - [ ] action blocked
  - [ ] receipt issued

## P1 — normalize receipt and manifest schemas

- [ ] Add `schemas/ink_manifest.v1.schema.json`.
- [ ] Add `schemas/ink_receipt.v1.schema.json`.
- [ ] Add `schemas/gate_decision.v1.schema.json`.
- [ ] Add `schemas/receipt_comparison.v1.schema.json`.
- [ ] Validate emitted artifacts against schemas during `demo`, `gate`, and `verify`.
- [ ] Add schema-version compatibility policy in docs.

## P1 — gate policy engine hardening

- [ ] Define first-class gate outcomes: `pass`, `warn`, `escalate`, `block`.
- [ ] Define required controls by risk tier:
  - [ ] low: trace only
  - [ ] medium: receipt required
  - [ ] high: receipt + human review
  - [ ] critical: receipt + human review + dual control
- [ ] Add policy fixtures for:
  - [ ] customer notice gate
  - [ ] claim denial gate
  - [ ] payment gate
  - [ ] underwriting recommendation gate
- [ ] Make `explain` output deterministic and receipt-grounded.

## P1 — repair docs to match the new product

- [ ] Rewrite `docs/public-object-spec.md` around BLKBX objects:
  - [ ] `ActionEvidenceBundle`
  - [ ] `GateAnalysisResult`
  - [ ] `InkReceiptResult`
  - [ ] `ReceiptComparisonPacket`
- [ ] Rewrite `docs/developer-architecture.md` around:
  - [ ] public facade: `blkbx_lab/`
  - [ ] internal trace layer
  - [ ] internal ink layer
  - [ ] internal gates layer
  - [ ] adapters
- [ ] Move old mechanistic interpretability content to `docs/research/`.
- [ ] Add `docs/migration-from-mech-lab.md`.

## P2 — compatibility and deprecation

- [ ] Add `mech_lab/__init__.py` shim importing from `blkbx_lab`.
- [ ] Add `mechlab` CLI alias only if needed for existing users.
- [ ] Emit deprecation warning: `mech_lab is deprecated; use blkbx_lab`.
- [ ] Emit CLI deprecation warning: `mechlab is deprecated; use blkbx-lab`.
- [ ] Set removal target: `0.2.0` or `0.3.0`.

## P2 — repository hygiene

- [ ] Add `TODO.md` at repo root.
- [ ] Add `CHANGELOG.md`.
- [ ] Add `CONTRIBUTING.md`.
- [ ] Add `SECURITY.md` explaining dev signing vs production signing.
- [ ] Add `.github/workflows/ci.yml`:
  - [ ] ruff
  - [ ] pyright
  - [ ] pytest
  - [ ] demo smoke test
  - [ ] verify/tamper smoke test
- [ ] Add release checklist.

## P2 — BLKBX commercial bridge

- [ ] Add doc: `docs/from-lab-to-blkbx.md`.
- [ ] State clearly:
  - [ ] BLKBX Lab creates local receipts.
  - [ ] BLKBX commercial stores evidence ledgers.
  - [ ] BLKBX commercial builds insurer-reviewable packets.
  - [ ] BLKBX Lab does not sell insurance and does not decide coverage.
- [ ] Add export placeholder:
  - [ ] `blkbx-lab export --format blkbx-packet`

## P3 — advanced interpretability module

- [ ] Preserve Qwen3.5 tract/bridge interpretation as optional advanced module.
- [ ] Keep metrics as optional evidence enrichments, not core SDK dependency:
  - [ ] bridge dependence
  - [ ] tract vs bridge report
  - [ ] compression-forgetting report
  - [ ] hook validation
- [ ] Add docs: `docs/research/qwen35-tract-bridge.md`.
- [ ] Ensure core BLKBX Lab works without model activations or CLTs.

## Release gates for `0.1.0a3`

- [ ] `pip install -e .` works.
- [ ] `blkbx-lab doctor` exits `0`.
- [ ] `blkbx-lab demo qwen35-claims --output-dir /tmp/qwen35-claims` works.
- [ ] `blkbx-lab verify /tmp/qwen35-claims/ink_receipt.v1.json` exits `0`.
- [ ] `blkbx-lab tamper /tmp/qwen35-claims/ink_receipt.v1.json` writes tampered receipt.
- [ ] `blkbx-lab verify /tmp/qwen35-claims/ink_receipt.tampered.json` exits nonzero.
- [ ] No public docs still describe the release identity as `mech-lab`.
- [ ] No generated public artifact contains `sha256:mock`.
- [ ] README, PyPI page, CLI contract, and developer architecture all agree on names.