use hm_core::family::TransportFamilyKind;
use hm_core::graph::Graph;
use hm_core::sketches::SignedSketch;
use hm_core::simplicial::SimplicialComplex;
use hm_std::exact_persistence::{compute_exact_persistence, ExactPersistenceInput};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

fn family_from_name(name: &str) -> PyResult<TransportFamilyKind> {
    match name {
        "gated_deltanet" => Ok(TransportFamilyKind::GatedDeltaNet),
        "hgrn2" => Ok(TransportFamilyKind::HGRN2),
        "retnet" => Ok(TransportFamilyKind::RetNet),
        "hawk" => Ok(TransportFamilyKind::Hawk),
        "transnormer_llm" => Ok(TransportFamilyKind::TransNormerLLM),
        "olmo_hybrid" => Ok(TransportFamilyKind::OLMoHybrid),
        "qwen35" => Ok(TransportFamilyKind::Qwen35),
        "kimi_linear" => Ok(TransportFamilyKind::KimiLinear),
        "custom" => Ok(TransportFamilyKind::Custom),
        _ => Err(PyValueError::new_err(format!("unknown family: {name}"))),
    }
}

#[pyfunction]
pub fn signed_sketch_from_counts(
    positive_components: u32,
    negative_components: u32,
    cancellation_pairs: u32,
    cycle_hint: u32,
) -> (u32, u32, u32, u32) {
    let sketch = SignedSketch {
        positive_components,
        negative_components,
        cancellation_pairs,
        cycle_hint,
    };
    (
        sketch.positive_components,
        sketch.negative_components,
        sketch.cancellation_pairs,
        sketch.cycle_hint,
    )
}

#[pyfunction]
#[allow(clippy::too_many_arguments)]
pub fn exact_persistence(
    family: &str,
    backend_name: &str,
    node_ids: Vec<u32>,
    edges: Vec<(u32, u32)>,
    vertex_filtration: Vec<f32>,
    edge_filtration: Vec<f32>,
    positive_components: u32,
    negative_components: u32,
    cancellation_pairs: u32,
    cycle_hint: u32,
    local_steps: usize,
    bridge_crossings: usize,
    retention_score: f32,
) -> PyResult<Vec<(u8, Vec<(f32, Option<f32>)>)>> {
    let input = ExactPersistenceInput {
        family: family_from_name(family)?,
        backend_name: backend_name.to_string(),
        graph: Graph {
            nodes: node_ids,
            edges,
        },
        complex: SimplicialComplex::default(),
        vertex_filtration,
        edge_filtration,
        signed_sketch: SignedSketch {
            positive_components,
            negative_components,
            cancellation_pairs,
            cycle_hint,
        },
        local_steps: local_steps as u32,
        bridge_crossings: bridge_crossings as u32,
        retention_score,
    };
    let report = compute_exact_persistence(&input);
    Ok(report
        .diagrams
        .into_iter()
        .map(|diagram| {
            (
                diagram.dimension,
                diagram
                    .pairs
                    .into_iter()
                    .map(|pair| (pair.birth, pair.death))
                    .collect(),
            )
        })
        .collect())
}
