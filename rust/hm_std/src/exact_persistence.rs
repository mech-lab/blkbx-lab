//! Deterministic offline persistence for small graph filtrations.

use std::collections::{BTreeMap, BTreeSet};

use hm_core::family::TransportFamilyKind;
use hm_core::graph::Graph;
use hm_core::simplicial::SimplicialComplex;
use hm_core::sketches::SignedSketch;

#[derive(Clone, Debug, PartialEq)]
pub struct ExactPersistenceInput {
    pub family: TransportFamilyKind,
    pub backend_name: String,
    pub graph: Graph,
    pub complex: SimplicialComplex,
    pub vertex_filtration: Vec<f32>,
    pub edge_filtration: Vec<f32>,
    pub signed_sketch: SignedSketch,
    pub local_steps: u32,
    pub bridge_crossings: u32,
    pub retention_score: f32,
}

#[derive(Clone, Debug, PartialEq)]
pub struct BirthDeathPair {
    pub dimension: u8,
    pub birth: f32,
    pub death: Option<f32>,
}

#[derive(Clone, Debug, PartialEq)]
pub struct PersistenceDiagram {
    pub dimension: u8,
    pub pairs: Vec<BirthDeathPair>,
}

#[derive(Clone, Debug, PartialEq)]
pub struct PersistenceSummary {
    pub h0_pairs: usize,
    pub h1_pairs: usize,
    pub infinite_pairs: usize,
    pub max_finite_persistence: f32,
    pub total_finite_persistence: f32,
}

#[derive(Clone, Debug, PartialEq)]
pub struct OfflineTopologyReport {
    pub family: TransportFamilyKind,
    pub backend_name: String,
    pub diagrams: Vec<PersistenceDiagram>,
    pub summary: PersistenceSummary,
}

#[derive(Clone, Debug)]
struct UnionFind {
    parent: Vec<usize>,
    birth: Vec<f32>,
}

impl UnionFind {
    fn new(births: &[f32]) -> Self {
        Self {
            parent: (0..births.len()).collect(),
            birth: births.to_vec(),
        }
    }

    fn find(&mut self, idx: usize) -> usize {
        if self.parent[idx] != idx {
            let root = self.find(self.parent[idx]);
            self.parent[idx] = root;
        }
        self.parent[idx]
    }

    fn union(&mut self, left: usize, right: usize) -> Option<(f32, f32)> {
        let left_root = self.find(left);
        let right_root = self.find(right);
        if left_root == right_root {
            return None;
        }
        let left_birth = self.birth[left_root];
        let right_birth = self.birth[right_root];
        if left_birth <= right_birth {
            self.parent[right_root] = left_root;
            self.birth[left_root] = left_birth.min(right_birth);
            Some((right_birth, left_birth))
        } else {
            self.parent[left_root] = right_root;
            self.birth[right_root] = left_birth.min(right_birth);
            Some((left_birth, right_birth))
        }
    }
}

pub fn compute_exact_persistence(input: &ExactPersistenceInput) -> OfflineTopologyReport {
    let nodes = normalized_nodes(input);
    let vertex_filtration = normalized_vertex_filtration(&nodes, &input.vertex_filtration);
    let node_positions: BTreeMap<u32, usize> = nodes
        .iter()
        .enumerate()
        .map(|(idx, node)| (*node, idx))
        .collect();
    let edge_entries = normalized_edges(input, &node_positions, &vertex_filtration);
    let mut union_find = UnionFind::new(&vertex_filtration);
    let mut h0_pairs = Vec::new();
    let mut h1_pairs = Vec::new();

    for (left, right, filtration) in edge_entries {
        match union_find.union(left, right) {
            Some((birth, _survivor_birth)) => {
                h0_pairs.push(BirthDeathPair {
                    dimension: 0,
                    birth,
                    death: Some(filtration),
                });
            }
            None => {
                h1_pairs.push(BirthDeathPair {
                    dimension: 1,
                    birth: filtration,
                    death: None,
                });
            }
        }
    }

    let mut roots = BTreeSet::new();
    for idx in 0..nodes.len() {
        roots.insert(union_find.find(idx));
    }
    for root in roots {
        h0_pairs.push(BirthDeathPair {
            dimension: 0,
            birth: union_find.birth[root],
            death: None,
        });
    }

    h0_pairs.sort_by(pair_sort_key);
    h1_pairs.sort_by(pair_sort_key);

    let summary = summarize(&h0_pairs, &h1_pairs);
    OfflineTopologyReport {
        family: input.family,
        backend_name: input.backend_name.clone(),
        diagrams: vec![
            PersistenceDiagram {
                dimension: 0,
                pairs: h0_pairs,
            },
            PersistenceDiagram {
                dimension: 1,
                pairs: h1_pairs,
            },
        ],
        summary,
    }
}

fn normalized_nodes(input: &ExactPersistenceInput) -> Vec<u32> {
    let mut nodes: Vec<u32> = input.graph.nodes.clone();
    if nodes.is_empty() {
        for (left, right) in &input.graph.edges {
            nodes.push(*left);
            nodes.push(*right);
        }
    }
    if nodes.is_empty() && !input.vertex_filtration.is_empty() {
        nodes.extend(0..input.vertex_filtration.len() as u32);
    }
    if nodes.is_empty() {
        nodes.push(0);
    }
    nodes.sort_unstable();
    nodes.dedup();
    nodes
}

fn normalized_vertex_filtration(nodes: &[u32], provided: &[f32]) -> Vec<f32> {
    if provided.len() == nodes.len() {
        return provided.to_vec();
    }
    let denom = (nodes.len() + 1) as f32;
    (0..nodes.len())
        .map(|idx| (idx as f32 + 1.0) / denom)
        .collect()
}

fn normalized_edges(
    input: &ExactPersistenceInput,
    node_positions: &BTreeMap<u32, usize>,
    vertex_filtration: &[f32],
) -> Vec<(usize, usize, f32)> {
    let mut edges = input.graph.edges.clone();
    edges.sort_unstable();
    edges.dedup();
    let edge_weights = if input.edge_filtration.len() == edges.len() {
        input.edge_filtration.clone()
    } else {
        let denom = (edges.len() + 1) as f32;
        edges
            .iter()
            .enumerate()
            .map(|(idx, (left, right))| {
                let left_idx = *node_positions.get(left).unwrap_or(&0);
                let right_idx = *node_positions.get(right).unwrap_or(&0);
                vertex_filtration[left_idx]
                    .max(vertex_filtration[right_idx])
                    + (idx as f32 + 1.0) / denom
            })
            .collect()
    };
    let mut entries: Vec<(usize, usize, f32)> = edges
        .into_iter()
        .enumerate()
        .map(|(idx, (left, right))| {
            let left_idx = *node_positions.get(&left).unwrap_or(&0);
            let right_idx = *node_positions.get(&right).unwrap_or(&0);
            let filtration = edge_weights[idx]
                .max(vertex_filtration[left_idx])
                .max(vertex_filtration[right_idx]);
            (left_idx, right_idx, filtration)
        })
        .collect();
    entries.sort_by(|a, b| {
        a.2.total_cmp(&b.2)
            .then_with(|| a.0.cmp(&b.0))
            .then_with(|| a.1.cmp(&b.1))
    });
    entries
}

fn pair_sort_key(left: &BirthDeathPair, right: &BirthDeathPair) -> std::cmp::Ordering {
    left.birth
        .total_cmp(&right.birth)
        .then_with(|| match (left.death, right.death) {
            (Some(left_death), Some(right_death)) => left_death.total_cmp(&right_death),
            (None, Some(_)) => std::cmp::Ordering::Greater,
            (Some(_), None) => std::cmp::Ordering::Less,
            (None, None) => std::cmp::Ordering::Equal,
        })
}

fn summarize(h0_pairs: &[BirthDeathPair], h1_pairs: &[BirthDeathPair]) -> PersistenceSummary {
    let mut infinite_pairs = 0usize;
    let mut max_finite_persistence = 0.0f32;
    let mut total_finite_persistence = 0.0f32;
    for pair in h0_pairs.iter().chain(h1_pairs.iter()) {
        match pair.death {
            Some(death) => {
                let persistence = death - pair.birth;
                if persistence > max_finite_persistence {
                    max_finite_persistence = persistence;
                }
                total_finite_persistence += persistence;
            }
            None => infinite_pairs += 1,
        }
    }
    PersistenceSummary {
        h0_pairs: h0_pairs.len(),
        h1_pairs: h1_pairs.len(),
        infinite_pairs,
        max_finite_persistence,
        total_finite_persistence,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_input(edges: Vec<(u32, u32)>) -> ExactPersistenceInput {
        ExactPersistenceInput {
            family: TransportFamilyKind::Qwen35,
            backend_name: "adapter".to_string(),
            graph: Graph {
                nodes: vec![0, 1, 2],
                edges,
            },
            complex: SimplicialComplex::default(),
            vertex_filtration: vec![0.0, 0.1, 0.2],
            edge_filtration: vec![0.3, 0.4, 0.5],
            signed_sketch: SignedSketch::default(),
            local_steps: 3,
            bridge_crossings: 1,
            retention_score: 0.8,
        }
    }

    #[test]
    fn path_graph_produces_h0_pairs() {
        let report = compute_exact_persistence(&sample_input(vec![(0, 1), (1, 2)]));
        assert_eq!(report.summary.h0_pairs, 3);
        assert_eq!(report.summary.h1_pairs, 0);
        assert_eq!(report.summary.infinite_pairs, 1);
    }

    #[test]
    fn cycle_graph_produces_h1_pair() {
        let report = compute_exact_persistence(&sample_input(vec![(0, 1), (1, 2), (0, 2)]));
        assert_eq!(report.summary.h1_pairs, 1);
        assert_eq!(report.diagrams[1].pairs[0].death, None);
    }

    #[test]
    fn persistence_is_deterministic() {
        let input = sample_input(vec![(0, 1), (1, 2), (0, 2)]);
        let left = compute_exact_persistence(&input);
        let right = compute_exact_persistence(&input);
        assert_eq!(left, right);
    }
}
