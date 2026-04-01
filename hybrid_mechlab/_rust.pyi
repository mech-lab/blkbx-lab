"""Type stub for the internal optional Rust shim."""

def available() -> bool: ...
def trace_schema_keys() -> list[str]: ...
def sparse_batch_summary(ids: list[int], values: list[float]) -> tuple[int, bool]: ...
def signed_sketch_from_counts(
    positive_components: int,
    negative_components: int,
    cancellation_pairs: int,
    cycle_hint: int,
) -> tuple[int, int, int, int]: ...
def bridge_dependence(local_steps: int, bridge_crossings: int) -> float: ...
def transport_digest(
    local_steps: int,
    bridge_crossings: int,
    prompt_count: int,
    backend_name: str,
) -> tuple[int, int, float]: ...
def exact_persistence(
    family: str,
    backend_name: str,
    node_ids: list[int],
    edges: list[tuple[int, int]],
    vertex_filtration: list[float],
    edge_filtration: list[float],
    positive_components: int,
    negative_components: int,
    cancellation_pairs: int,
    cycle_hint: int,
    local_steps: int,
    bridge_crossings: int,
    retention_score: float,
) -> list[tuple[int, list[tuple[float, float | None]]]]: ...
