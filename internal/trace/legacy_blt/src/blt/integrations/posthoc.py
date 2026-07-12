from __future__ import annotations

from pathlib import Path
import tempfile

from blt.export import run_trace


def materialize_trace_artifacts(
    trace_id: str,
    prompt: str,
    *,
    output_root: str | Path | None = None,
    backend: str = "mock",
    profile: str | Path | dict[str, object] | None = None,
    model_family: str | None = None,
    model_variant: str | None = None,
) -> Path:
    root = Path(output_root) if output_root is not None else Path(tempfile.gettempdir()) / "posthoc_blt_traces"
    run_dir = root / trace_id
    return run_trace(
        prompt=prompt,
        trace_id=trace_id,
        output_dir=run_dir,
        backend=backend,
        profile=profile,
        model_family=model_family,
        model_variant=model_variant,
        producer="blt:posthoc:0.1.0",
    )
