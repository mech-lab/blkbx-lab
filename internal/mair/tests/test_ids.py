from mair.ids import derive_artifact_id, stable_hash


def test_stable_hash_is_deterministic() -> None:
    payload = {"b": 2, "a": 1}
    assert stable_hash(payload) == stable_hash({"a": 1, "b": 2})


def test_derive_artifact_id_is_stable() -> None:
    content_hash = stable_hash({"artifact": "demo"})
    assert derive_artifact_id("mair_graph_ir", content_hash) == derive_artifact_id("mair_graph_ir", content_hash)
