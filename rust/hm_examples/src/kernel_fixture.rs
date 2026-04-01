use hm_core::family::{descriptor_for, TransportFamilyKind, TransportRegimeKind};
use hm_core::graph::Graph;
use hm_core::native::{gated_deltanet_kernel, validate_kernel, NativeTransportKernel};
use hm_core::schedule::{BlockOp, HybridSchedule};
use hm_core::simplicial::SimplicialComplex;
use hm_core::sketches::SignedSketch;
use hm_std::exact_persistence::{compute_exact_persistence, ExactPersistenceInput};
use serde_json::json;

fn round_to(value: f32, places: f32) -> f32 {
    (value * places).round() / places
}

fn transport_digest(
    local_steps: usize,
    bridge_crossings: usize,
    prompt_count: usize,
    backend_name: &str,
) -> (usize, usize, f32) {
    let multiplier = prompt_count.max(1);
    let total_local_steps = local_steps * multiplier;
    let total_bridge_crossings = bridge_crossings * multiplier;
    let backend_factor = match backend_name {
        "adapter" => 0.86,
        "native" => 1.0,
        "liger" => 0.94,
        _ => 1.0,
    };
    let retention = ((total_local_steps + 1) as f32
        / (total_local_steps + total_bridge_crossings + 1) as f32)
        * backend_factor;
    (
        total_local_steps,
        total_bridge_crossings,
        round_to(retention, 10_000.0),
    )
}

fn qwen35_schedule() -> HybridSchedule {
    let descriptor = descriptor_for(TransportFamilyKind::Qwen35);
    let bridge = descriptor.bridge;
    HybridSchedule {
        descriptor,
        cadence_label: "3:1",
        ops: vec![
            BlockOp {
                kind: TransportRegimeKind::RecurrentTransport,
                local_index: 0,
                repeats: 1,
                label: "Qwen3.5",
                bridge: None,
            },
            BlockOp {
                kind: TransportRegimeKind::RecurrentTransport,
                local_index: 1,
                repeats: 1,
                label: "Qwen3.5",
                bridge: None,
            },
            BlockOp {
                kind: TransportRegimeKind::RecurrentTransport,
                local_index: 2,
                repeats: 1,
                label: "Qwen3.5",
                bridge: None,
            },
            BlockOp {
                kind: TransportRegimeKind::GlobalBridge,
                local_index: 3,
                repeats: 1,
                label: "Qwen3.5",
                bridge,
            },
        ],
    }
}

fn build_graph(schedule: &HybridSchedule, cancellation_pairs: u32) -> (Graph, Vec<(u32, u32)>, Vec<(u32, u32)>) {
    let node_ids: Vec<u32> = (0..=(schedule.ops.len() as u32)).collect();
    let last_node = *node_ids.last().unwrap_or(&0);
    let path_edges: Vec<(u32, u32)> = (0..last_node).map(|idx| (idx, idx + 1)).collect();
    let bridge_edges: Vec<(u32, u32)> = schedule
        .ops
        .iter()
        .filter(|op| matches!(op.kind, TransportRegimeKind::GlobalBridge))
        .filter_map(|op| {
            let node = op.local_index as u32 + 1;
            if node < node_ids.len() as u32 {
                Some((0, node))
            } else {
                None
            }
        })
        .collect();
    let mut edges = path_edges.clone();
    edges.append(&mut bridge_edges.clone());
    if cancellation_pairs > 0 && last_node >= 3 {
        edges.push((1, last_node));
    }
    edges.sort_unstable();
    edges.dedup();
    (
        Graph {
            nodes: node_ids,
            edges,
        },
        path_edges,
        bridge_edges,
    )
}

fn vertex_filtration(node_count: usize, retention_score: f32) -> Vec<f32> {
    let denom = (node_count + 1) as f32;
    let scale = 1.0 - (retention_score * 0.15);
    (0..node_count)
        .map(|idx| round_to((((idx + 1) as f32) / denom) * scale, 1_000_000.0))
        .collect()
}

fn edge_filtration(
    edge_list: &[(u32, u32)],
    path_edges: &[(u32, u32)],
    bridge_edges: &[(u32, u32)],
    local_steps: usize,
    bridge_crossings: usize,
    retention_score: f32,
    cancellation_pairs: u32,
    vertex_values: &[f32],
) -> Vec<f32> {
    let denom = (edge_list.len() + 1).max(1) as f32;
    let bridge_dependence = bridge_crossings as f32 / (local_steps + bridge_crossings).max(1) as f32;
    edge_list
        .iter()
        .enumerate()
        .map(|(idx, edge)| {
            let base = vertex_values[edge.0 as usize].max(vertex_values[edge.1 as usize]);
            let offset = if bridge_edges.contains(edge) {
                0.1 + (bridge_dependence * 0.1)
            } else if path_edges.contains(edge) {
                0.03 + (retention_score * 0.03)
            } else {
                0.12 + (cancellation_pairs as f32 * 0.01)
            };
            let step = (idx as f32 + 1.0) / denom;
            round_to(base + offset + step * 0.02, 1_000_000.0)
        })
        .collect()
}

fn profile_fixture(
    family_name: &str,
    backend_name: &str,
    schedule: &HybridSchedule,
    prompt_count: usize,
    cancellation_pairs: u32,
) -> serde_json::Value {
    let local_steps = schedule.ops.len() - schedule.bridge_count();
    let bridge_crossings = schedule.bridge_count();
    let (total_local_steps, total_bridge_crossings, retention_score) =
        transport_digest(local_steps, bridge_crossings, prompt_count, backend_name);
    let sketch = SignedSketch {
        positive_components: total_local_steps as u32,
        negative_components: bridge_crossings.saturating_sub(1) as u32,
        cancellation_pairs,
        cycle_hint: bridge_crossings.saturating_sub(1) as u32,
    };
    let (graph, path_edges, bridge_edges) = build_graph(schedule, cancellation_pairs);
    let vertex_values = vertex_filtration(graph.nodes.len(), retention_score);
    let edge_values = edge_filtration(
        &graph.edges,
        &path_edges,
        &bridge_edges,
        total_local_steps,
        total_bridge_crossings,
        retention_score,
        cancellation_pairs,
        &vertex_values,
    );
    let report = compute_exact_persistence(&ExactPersistenceInput {
        family: if family_name == "qwen35" {
            TransportFamilyKind::Qwen35
        } else {
            TransportFamilyKind::GatedDeltaNet
        },
        backend_name: backend_name.to_string(),
        graph: graph.clone(),
        complex: SimplicialComplex::default(),
        vertex_filtration: vertex_values.clone(),
        edge_filtration: edge_values.clone(),
        signed_sketch: sketch,
        local_steps: total_local_steps as u32,
        bridge_crossings: total_bridge_crossings as u32,
        retention_score,
    });
    let conformance = if family_name == "qwen35" {
        schedule.conformance()
    } else {
        validate_kernel(&gated_deltanet_kernel())
    };
    json!({
        "family": family_name,
        "backend": backend_name,
        "schedule": {
            "rows": schedule.ops.iter().map(|op| json!([format!("{:?}", op.kind), op.local_index])).collect::<Vec<_>>(),
            "conformance": {
                "passed": conformance.passed,
                "schedule_length": conformance.schedule_length,
                "bridge_count": conformance.bridge_count
            }
        },
        "transport_digest": {
            "local_steps": total_local_steps,
            "bridge_crossings": total_bridge_crossings,
            "retention_score": retention_score
        },
        "persistence_input": {
            "node_ids": graph.nodes,
            "edge_list": graph.edges,
            "vertex_filtration": vertex_values,
            "edge_filtration": edge_values
        },
        "diagrams": report.diagrams.iter().map(|diagram| {
            json!({
                "dimension": diagram.dimension,
                "pairs": diagram.pairs.iter().map(|pair| json!({
                    "birth": pair.birth,
                    "death": pair.death
                })).collect::<Vec<_>>()
            })
        }).collect::<Vec<_>>(),
        "summary": {
            "h0_pairs": report.summary.h0_pairs,
            "h1_pairs": report.summary.h1_pairs,
            "infinite_pairs": report.summary.infinite_pairs,
            "max_finite_persistence": report.summary.max_finite_persistence,
            "total_finite_persistence": report.summary.total_finite_persistence
        }
    })
}

fn main() {
    let qwen = qwen35_schedule();
    let gated = gated_deltanet_kernel();
    let fixture = json!({
        "profiles": {
            "qwen35": profile_fixture("qwen35", "adapter", &qwen, 1, 0),
            "gated_deltanet": profile_fixture("gated_deltanet", "native", gated.schedule(), 1, 0)
        }
    });
    println!("{}", serde_json::to_string_pretty(&fixture).unwrap());
}
