from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from hybrid_mechlab._mair import ensure_mair_importable
from hybrid_mechlab.api import ReproducibilityManifest, SignedSketchRecord, TraceHandle, TransportDigest
from hybrid_mechlab.profiles import BackendKind, ResearchProfile, resolve_profile
from hybrid_mechlab.schedules import (
    TransportFamilyKind,
    TransportRegimeKind,
    custom_schedule,
    family_descriptor,
)

ensure_mair_importable()
from mair.hydrate import load_artifact_bundle  # noqa: E402


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 6) if values else 0.0


def _normalize_family_name(raw: str | None) -> str:
    return (raw or "").strip().lower().replace("-", "_").replace(".", "")


def _infer_family_kind(raw: str | None) -> TransportFamilyKind:
    normalized = _normalize_family_name(raw)
    aliases = {
        "qwen35": TransportFamilyKind.qwen35,
        "qwen35_hybrid": TransportFamilyKind.qwen35,
        "qwen35hybrid": TransportFamilyKind.qwen35,
        "qwen_hybrid": TransportFamilyKind.qwen35,
        "qwen35hybridadapter": TransportFamilyKind.qwen35,
        "qwen35hybridnative": TransportFamilyKind.qwen35,
        "qwen35hybridliger": TransportFamilyKind.qwen35,
        "qwen35hybridmock": TransportFamilyKind.qwen35,
        "qwen35hybridqwen_hybrid_hf": TransportFamilyKind.qwen35,
        "gated_deltanet": TransportFamilyKind.gated_deltanet,
        "hgrn2": TransportFamilyKind.hgrn2,
        "retnet": TransportFamilyKind.retnet,
        "hawk": TransportFamilyKind.hawk,
        "transnormer_llm": TransportFamilyKind.transnormer_llm,
        "olmohybrid": TransportFamilyKind.olmo_hybrid,
        "olmo_hybrid": TransportFamilyKind.olmo_hybrid,
        "kimilinear": TransportFamilyKind.kimi_linear,
        "kimi_linear": TransportFamilyKind.kimi_linear,
    }
    return aliases.get(normalized, TransportFamilyKind.custom)


def _canonical_backend(family: TransportFamilyKind, source_backend: str) -> BackendKind:
    normalized = source_backend.strip().lower()
    if normalized in {member.value for member in BackendKind}:
        return BackendKind(normalized)
    if family in {TransportFamilyKind.qwen35, TransportFamilyKind.olmo_hybrid, TransportFamilyKind.kimi_linear}:
        return BackendKind.adapter
    return BackendKind.native


def _profile_for_import(
    *,
    trace_id: str,
    family_kind: TransportFamilyKind,
    source_backend: str,
    profile_name: str | None,
    graph_ir: dict[str, Any],
) -> ResearchProfile:
    canonical_backend = _canonical_backend(family_kind, source_backend)
    if family_kind == TransportFamilyKind.custom:
        descriptor = family_descriptor(TransportFamilyKind.custom)
        schedule = custom_schedule(
            (
                TransportRegimeKind.recurrent_transport,
                TransportRegimeKind.recurrent_transport,
                TransportRegimeKind.recurrent_transport,
                TransportRegimeKind.global_bridge,
            ),
            family=descriptor,
            cadence_label="mair-import",
        )
        return ResearchProfile(
            name=profile_name or f"mair.{trace_id}",
            family=descriptor,
            schedule=schedule,
            backend=canonical_backend,
            hook_points=("block.recurrent", "block.bridge"),
            metadata={"source": "mair", "capture_backend": source_backend, "mair_graph_ir": graph_ir},
        )

    resolved = resolve_profile(family_kind, canonical_backend)
    return ResearchProfile(
        name=profile_name or resolved.name,
        family=resolved.family,
        schedule=resolved.schedule,
        backend=resolved.backend,
        hook_points=resolved.hook_points,
        source_adapter=resolved.source_adapter,
        metadata={**resolved.metadata, "source": "mair", "capture_backend": source_backend, "mair_graph_ir": graph_ir},
    )


def _capture_surfaces(artifact_payloads: dict[str, Any]) -> tuple[str, ...]:
    capture: list[str] = []
    if "blt_codes" in artifact_payloads:
        capture.append("codes")
    if "topology_summary" in artifact_payloads:
        capture.append("sketches")
    if "tract_state_snapshot" in artifact_payloads or "mair_semantic_trace" in artifact_payloads:
        capture.append("transport")
    if "grouped_clt_bundle" in artifact_payloads:
        capture.append("grouped_clt")
    return tuple(capture)


def _transport_digest(
    *,
    backend: str,
    topology_summary: dict[str, Any],
    semantic_rows: list[dict[str, Any]],
    tract_rows: list[dict[str, Any]],
    blt_code_rows: list[dict[str, Any]],
) -> TransportDigest:
    bridge_crossings = sum(1 for row in semantic_rows if row.get("op") == "BridgeApply")
    local_steps = len(tract_rows) if tract_rows else sum(1 for row in semantic_rows if row.get("op") == "StateUpdate")
    retention_score = topology_summary.get("tract_retention")
    if retention_score is None:
        retention_score = max(0.0, 1.0 - _mean([float(row["reconstruction_error"]) for row in blt_code_rows]))
    return TransportDigest(
        local_steps=int(local_steps),
        bridge_crossings=int(bridge_crossings),
        retention_score=round(float(retention_score), 6),
        backend=backend,
    )


def _signed_sketch(topology_summary: dict[str, Any], intervention_rows: list[dict[str, Any]]) -> SignedSketchRecord:
    summary_metrics = topology_summary.get("summary_metrics") or {}
    component_count = max(int(summary_metrics.get("component_count", 1)), 1)
    mean_degree = float(summary_metrics.get("mean_degree", 0.0))
    return SignedSketchRecord(
        positive_components=component_count,
        negative_components=0,
        cancellation_pairs=len(intervention_rows),
        cycle_hint=max(int(round(mean_degree)) - 1, 0),
    )


def _schedule_hash(schedule_summary: str, trace_id: str, backend: str) -> str:
    return hashlib.sha256(f"{trace_id}|{backend}|{schedule_summary}".encode("utf-8")).hexdigest()[:16]


def _reproducibility_manifest(
    *,
    trace_id: str,
    model: str,
    profile_name: str,
    family: str,
    backend: str,
    schedule_summary: str,
) -> ReproducibilityManifest:
    return ReproducibilityManifest(
        model=model or trace_id,
        profile_name=profile_name,
        family=family,
        backend=backend,
        schedule_hash=_schedule_hash(schedule_summary, trace_id, backend),
    )


def _sparse_codes(blt_code_rows: list[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    by_block: dict[str, list[dict[str, Any]]] = {}
    for row in blt_code_rows:
        by_block.setdefault(str(row["block_id"]), []).append(row)
    records: list[dict[str, Any]] = []
    for block_id, members in sorted(by_block.items()):
        records.append(
            {
                "hook": f"{block_id}.post_d3",
                "feature_ids": [0, 1, 2, 3],
                "feature_values": [
                    _mean([float(member[column]) for member in members])
                    for column in ("code_0", "code_1", "code_2", "code_3")
                ],
            }
        )
    return tuple(records)


def load_trace_from_mair_manifest(manifest_path: str | Path) -> TraceHandle:
    bundle = load_artifact_bundle(manifest_path)
    manifest = bundle["manifest"]
    artifacts = bundle["artifacts"]
    graph_ir = artifacts["mair_graph_ir"]
    numeric_lowering = artifacts.get("mair_numeric_lowering", {})
    topology_summary = artifacts.get("topology_summary", {})
    semantic_rows = artifacts.get("mair_semantic_trace", [])
    tract_rows = artifacts.get("tract_state_snapshot", [])
    blt_code_rows = artifacts.get("blt_codes", [])
    intervention_rows = artifacts.get("intervention_sweep", [])

    source_backend = str(graph_ir.get("capture_backend") or numeric_lowering.get("backend") or "mair-import")
    family_kind = _infer_family_kind(graph_ir.get("model_family"))
    profile_name = str(graph_ir.get("profile_id") or numeric_lowering.get("profile_id") or f"mair.{manifest['trace_id']}")
    profile = _profile_for_import(
        trace_id=manifest["trace_id"],
        family_kind=family_kind,
        source_backend=source_backend,
        profile_name=profile_name,
        graph_ir=graph_ir,
    )
    schedule_summary = profile.schedule.summary()

    return TraceHandle(
        trace_id=manifest["trace_id"],
        prompts=(f"mair::{manifest['trace_id']}",),
        profile=profile,
        backend=source_backend,
        math_backend="python",
        schedule=profile.schedule,
        sparse_codes=_sparse_codes(blt_code_rows),
        signed_sketch=_signed_sketch(topology_summary, intervention_rows),
        transport_digest=_transport_digest(
            backend=source_backend,
            topology_summary=topology_summary,
            semantic_rows=semantic_rows,
            tract_rows=tract_rows,
            blt_code_rows=blt_code_rows,
        ),
        reproducibility_manifest=_reproducibility_manifest(
            trace_id=manifest["trace_id"],
            model=str(graph_ir.get("model_variant", manifest["trace_id"])),
            profile_name=profile.name,
            family=profile.family.kind.value,
            backend=source_backend,
            schedule_summary=schedule_summary,
        ),
        capture=_capture_surfaces(artifacts),
        interventions=tuple(intervention_rows),
    )
