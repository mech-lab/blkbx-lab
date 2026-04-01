# hybrid-mechlab

**A reusable research-grade Python SDK with Rust bindings for mathematically rigorous hybrid-model research.**  
**Primary posture:** Python-first experimentation, Rust-first math core, model-family-agnostic hybrid instrumentation, and a `no_std` kernel for transport, topology, and block/layer geometry.

---

## Status

This file is the **single flattened project document** for the initial repository. It serves as:

1. the top-level `README.md`,
2. the technical architecture specification,
3. the flattened project manifest,
4. the binding contract between Python and Rust,
5. the research roadmap for hybrid-model mechanistic understanding.

It **explicitly integrates and generalizes** the seed design from the attached document **“Block-Level Transcoder and TDA Sidecar for Hybrid 3:1 Architectures”** into a broader, reusable Python SDK project. The original 3:1 design is retained as the first flagship profile, but the system is extended to support **ratio-agnostic hybrid schedules** such as **2:1, 3:1, 4:1, 7:1**, and arbitrary user-defined recurrent/attention block rhythms.

---

## Executive Summary

`hybrid-mechlab` is a **model-family-agnostic SDK for hybrid-model research** that treats hybrid networks as **structured transport systems** rather than opaque tensor stacks.

The core design move is simple:

- keep the **research interface** in Python,
- keep the **mathematical kernel** in Rust,
- keep the **Rust kernel `no_std` by default**,
- make topology, geometry, sheaf-like transport, and block/layer relations first-class,
- make model-specific details live in **adapter profiles**, not in the core math.

The project is built for hybrid families that interleave:
- recurrent or linear-memory sublayers,
- periodic global-attention bridges,
- feed-forward integration stages,
- and optional gating layers.

The first target profile is a **Qwen3.5-style 3:1 hybrid rhythm**, but the SDK is intentionally designed so a researcher can swap in:
- **2:1**
- **3:1**
- **4:1**
- **7:1**
- or custom schedules

without rewriting the topology, transport, or analysis stack.

The Python SDK is where the researcher works:
- attaching hooks,
- collecting traces,
- running experiments,
- exporting artifacts,
- performing interventions,
- training block-level transcoders,
- and comparing hybrid ratios across model families.

The Rust core is where mathematical discipline lives:
- typed transport objects,
- sparse feature-state containers,
- filtration and graph primitives,
- partial-sheaf interfaces,
- connection and holonomy abstractions,
- signed topological sketch interfaces,
- Mapper and persistence stubs,
- deterministic serialization and hashing.

The result is not just another interpretability wrapper. It is a **research substrate for mathematically structured mechanistic understanding**.

---

## Design Goals

### Primary goals

- **Model-family-agnostic hybrid research**
  - Support families with repeated recurrent/linear-memory tracts and periodic attention bridges.
- **Python ergonomics**
  - Fast research iteration, notebooks, plotting, experiment orchestration, and adapter authoring.
- **Rust mathematical core**
  - Deterministic, typed, auditable numerical and combinatorial kernels.
- **`no_std` first**
  - The portable kernel should not depend on OS, filesystem, or network facilities.
- **Ratio-agnostic block scheduling**
  - Support `k:1` hybrid rhythms and arbitrary schedules.
- **Mathematical rigor**
  - Treat block relations as transport/connection problems, not just activation logging.
- **Topology-ready by construction**
  - Persistent homology, Mapper, and related structures begin as **stable stubs and traits** in the kernel.
- **Research-grade replacement-model tooling**
  - Support block-level transcoders, sparse codes, interventions, attribution exports, and reproducibility.
- **Separation of concerns**
  - Model adapters, plotting, training harnesses, and data loading stay in Python.
  - Core math and stable data contracts stay in Rust.

### Non-goals

- This is **not** a new foundation model architecture.
- This is **not** a monolithic training framework.
- This is **not** a production inference stack.
- This is **not** a full persistent-homology engine inside the `no_std` kernel.
- This is **not** a claim that topology alone yields mechanistic truth.

---

## Core Thesis

Hybrid models are easier to study when they are represented as a **typed sequence of transport regimes**.

Instead of asking only:

- Which neuron fired?
- Which feature activated?
- Which layer mattered?

we ask:

- What **transport law** maps one block-local state to the next?
- Where does information remain within a **local tract**?
- Where does it cross a **global bridge**?
- What **connection** is induced between block-level feature bundles?
- What breaks when those connections are perturbed?
- Which topological summaries are stable across prompts, seeds, and intervention strengths?

This project exists to make those questions operational.

---

## Integrated Seed Design: BLT + TDA Sidecar

The attached 3:1 design document becomes the seed profile of this repository.

That seed contributes five enduring concepts:

1. **Block-Level Transcoder (BLT)**
   - A replacement-model-capable instrumentation layer that converts block flows into sparse codes and tract summaries.

2. **Hybrid tracts and bridges**
   - Recurrent or linear-memory sublayers are treated as **tracts**.
   - Periodic full-attention sublayers are treated as **bridges**.

3. **Topological sidecar**
   - Lightweight online sketches during tracing.
   - Exact or heavier topological computation offline.

4. **Intervention bifiltration**
   - Track behavior jointly across **scale** and **intervention strength**.

5. **Compatibility with existing interpretability ecosystems**
   - Sparse codes and exports should interoperate with replacement-model and attribution-graph workflows.

This repository preserves those ideas but lifts them out of the fixed 3:1 case.

---

## High-Level Architecture

```text
Python Research SDK
├── model adapters
├── hook orchestration
├── experiment configs
├── training utilities
├── visualization
├── dataset/export utilities
└── FFI bindings

Rust Math Core (`no_std`)
├── core algebra and sparse containers
├── hybrid schedule IR
├── transport / connection traits
├── partial-sheaf interfaces
├── graph / hypergraph / simplicial primitives
├── signed topology sketch traits
├── Mapper / persistence stubs
├── deterministic codecs / hashing
└── optional alloc/std extension points

Optional Rust std crates
├── exact topology engines
├── parquet / zarr / arrow IO
├── heavy offline audits
└── performance kernels
```

---

## Flattened Repository Manifest

```text
hybrid-mechlab/
├─ README.md                                  # this flattened file
├─ pyproject.toml                             # python packaging + maturin
├─ Cargo.toml                                 # rust workspace root
├─ LICENSE
├─ .gitignore
├─ hybrid_mechlab/
│  ├─ __init__.py
│  ├─ api.py                                  # primary user API
│  ├─ config.py                               # typed experiment configs
│  ├─ registry.py                             # model/profile registry
│  ├─ schedules.py                            # ratio and custom schedule helpers
│  ├─ adapters/
│  │  ├─ __init__.py
│  │  ├─ base.py                              # abstract hybrid adapter
│  │  ├─ qwen35.py                            # Qwen3.5-style 3:1 adapter
│  │  ├─ qwen3next.py                         # optional Qwen3-Next adapter
│  │  ├─ olmo_hybrid.py
│  │  ├─ kimi_linear.py
│  │  └─ custom.py
│  ├─ hooks/
│  │  ├─ __init__.py
│  │  ├─ capture.py                           # activation and state capture
│  │  ├─ replay.py
│  │  ├─ interventions.py
│  │  └─ policies.py
│  ├─ blt/
│  │  ├─ __init__.py
│  │  ├─ encoder.py                           # python trainer/wrapper for BLT encoders
│  │  ├─ decoder.py
│  │  ├─ replacement.py                       # replacement-model semantics
│  │  ├─ sparse_codes.py
│  │  └─ exporters.py
│  ├─ topology/
│  │  ├─ __init__.py
│  │  ├─ online.py                            # online sketch wrappers
│  │  ├─ offline.py                           # offline PH/Mapper orchestration
│  │  ├─ sheaf.py                             # high-level sheaf/connection utilities
│  │  ├─ block_graphs.py
│  │  └─ metrics.py                           # susceptibility, bridge dependence, etc.
│  ├─ experiments/
│  │  ├─ __init__.py
│  │  ├─ sweep.py
│  │  ├─ long_context.py
│  │  ├─ concept_evolution.py
│  │  └─ bridge_penalty.py
│  ├─ viz/
│  │  ├─ __init__.py
│  │  ├─ block_maps.py
│  │  ├─ persistence.py
│  │  ├─ mapper.py
│  │  ├─ transport.py
│  │  └─ dashboards.py
│  ├─ io/
│  │  ├─ __init__.py
│  │  ├─ jsonl.py
│  │  ├─ parquet.py
│  │  ├─ zarr.py
│  │  └─ manifests.py
│  ├─ cli.py
│  └─ _rust.pyi
├─ rust/
│  ├─ hm_core/                                # no_std kernel
│  │  ├─ Cargo.toml
│  │  └─ src/
│  │     ├─ lib.rs
│  │     ├─ prelude.rs
│  │     ├─ scalar.rs
│  │     ├─ sparse.rs
│  │     ├─ ids.rs
│  │     ├─ hash.rs
│  │     ├─ fixed.rs
│  │     ├─ schedule.rs
│  │     ├─ hooks.rs
│  │     ├─ transport.rs
│  │     ├─ connection.rs
│  │     ├─ sheaf.rs
│  │     ├─ graph.rs
│  │     ├─ hypergraph.rs
│  │     ├─ simplicial.rs
│  │     ├─ filtrations.rs
│  │     ├─ topology.rs
│  │     ├─ mapper.rs
│  │     ├─ persistence.rs
│  │     ├─ sketches.rs
│  │     ├─ metrics.rs
│  │     ├─ ir.rs
│  │     ├─ codec.rs
│  │     └─ errors.rs
│  ├─ hm_std/
│  │  ├─ Cargo.toml
│  │  └─ src/
│  │     ├─ lib.rs
│  │     ├─ exact_persistence.rs
│  │     ├─ mapper_exec.rs
│  │     ├─ io_arrow.rs
│  │     ├─ io_parquet.rs
│  │     ├─ io_zarr.rs
│  │     ├─ audit.rs
│  │     └─ benches.rs
│  ├─ hm_pyo3/
│  │  ├─ Cargo.toml
│  │  └─ src/
│  │     ├─ lib.rs
│  │     ├─ py_schedule.rs
│  │     ├─ py_trace.rs
│  │     ├─ py_sparse.rs
│  │     ├─ py_topology.rs
│  │     └─ py_metrics.rs
│  └─ hm_examples/
│     ├─ Cargo.toml
│     └─ src/
│        └─ qwen35_profile.rs
├─ specs/
│  ├─ hybrid_schedule_v1.md
│  ├─ blt_trace_v1.md
│  ├─ sparse_codes_v1.md
│  ├─ topology_sketch_v1.md
│  ├─ sheaf_connection_v1.md
│  ├─ intervention_protocol_v1.md
│  └─ replacement_model_v1.md
├─ notebooks/
│  ├─ 00_qwen35_attach.ipynb
│  ├─ 01_block_maps.ipynb
│  ├─ 02_bifiltration.ipynb
│  ├─ 03_concept_evolution.ipynb
│  └─ 04_ratio_comparison.ipynb
└─ tests/
   ├─ test_schedule_profiles.py
   ├─ test_trace_roundtrip.py
   ├─ test_sparse_code_roundtrip.py
   ├─ test_bridge_dependence.py
   ├─ test_partial_sheaf_contracts.py
   └─ test_replacement_mode.py
```

---

## Why Python + Rust

### Python side
Python remains the fastest surface for:
- model loading,
- hook attachment,
- experiment control,
- plotting,
- notebooks,
- training loops,
- and interop with the research ecosystem.

### Rust side
Rust owns:
- deterministic contracts,
- stable typed IDs,
- exact serialization,
- sparse-state kernels,
- block/layer schedule semantics,
- topology and geometry traits,
- and memory-safe low-level code.

### Why `no_std`
The math kernel should not assume:
- heap-rich environments,
- the presence of a filesystem,
- or a particular runtime.

That makes the kernel:
- portable,
- testable,
- embeddable,
- and more suitable for later assurance-oriented uses.

---

## Primary Concepts

## 1. Hybrid Schedule

A hybrid model is represented as a typed **schedule** rather than implicitly via layer indices.

```rust
pub enum BlockOpKind {
    RecurrentTransport,
    GlobalBridge,
    FeedForward,
    Norm,
    ResidualAdd,
    Gate,
    Other,
}

pub struct BlockOp {
    pub kind: BlockOpKind,
    pub local_index: u16,
    pub repeats: u16,
    pub label: &'static str,
}

pub struct HybridSchedule<const MAX_OPS: usize> {
    pub ops: heapless::Vec<BlockOp, MAX_OPS>,
}
```

This lets us define:
- 2:1
- 3:1
- 4:1
- irregular patterns
- model-family-specific schedules

without changing higher-level math.

### Example schedule profiles

```python
from hybrid_mechlab.schedules import ratio_schedule

sched_3_1 = ratio_schedule(recurrent=3, bridge=1)
sched_4_1 = ratio_schedule(recurrent=4, bridge=1)
sched_2_1 = ratio_schedule(recurrent=2, bridge=1)
```

### Design rule
**The math core sees schedules, not vendor names.**

---

## 2. Blocks, Layers, and Regimes

The project distinguishes:

- **Layer**
  - a physical model layer index.
- **Block**
  - a logical research unit, potentially spanning multiple physical sublayers.
- **Regime**
  - a local computational mode such as recurrent transport or global attention.
- **Tract**
  - a contiguous sequence of recurrent/linear-memory regime steps.
- **Bridge**
  - a global-attention or equivalent synchronizing step.

This separation is essential because a hybrid model should not be analyzed as if every layer were semantically equivalent.

---

## 3. Block-Level Transcoder (BLT)

The BLT is the interpretable replacement-model layer.

Its job is to:
- attach to hook points,
- encode activations/states into sparse features,
- decode sparse features back into approximations,
- and preserve enough semantics for interventions and attribution.

### BLT requirements

- model-family-agnostic hook contract,
- sparse-code-first design,
- block-aware semantics,
- replayable exports,
- optional learned encoders/decoders,
- support for both research tracing and replacement-mode execution.

### BLT contract

```python
class BLTEncoder(Protocol):
    def encode(self, hook_state) -> "SparseCodeBatch": ...

class BLTDecoder(Protocol):
    def decode(self, codes, target_hook: str): ...

class ReplacementModel(Protocol):
    def forward_with_replacement(self, batch, replacement_policy): ...
```

### First-class outputs

1. **Sparse codes**
2. **Transport summaries**
3. **Topology sketches**
4. **Replacement-mode divergence metrics**
5. **Attribution export graphs**

---

## 4. Partial Sheaves and Connections

This repository uses **partial sheaf-like structures** as a research abstraction for relating information between blocks, hook points, and local feature spaces.

### Why partial sheaves
In real mechanistic research:
- you do not always have complete coverage,
- restrictions are often approximate,
- overlap maps may be partial,
- and exact sheaf conditions may fail in structured ways.

So the project uses **partial sheaf contracts** rather than pretending every block relation is exact.

### Core idea

A partial sheaf in this SDK is:

- a family of local sections attached to blocks or hook regions,
- partial restriction maps between them,
- optional consistency scores,
- and failure objects when gluing does not succeed.

### Rust kernel interface

```rust
pub trait PartialSection {
    type Id: Copy;
    type Value;
    fn id(&self) -> Self::Id;
    fn value(&self) -> &Self::Value;
}

pub trait RestrictionMap<S: PartialSection> {
    type Error;
    fn restrict(&self, src: &S) -> Result<S, Self::Error>;
}

pub trait PartialSheaf<S: PartialSection, R: RestrictionMap<S>> {
    fn local_sections(&self) -> &[S];
    fn restrictions(&self) -> &[R];
}
```

### Connection view
We also want block-to-block **connection-like structure**:

- transport across recurrent tracts,
- jump conditions at bridges,
- compatibility measures across scales,
- holonomy-style failure around loops in block graphs.

This is especially useful for:
- concept evolution,
- path dependence,
- loop inconsistency,
- and cross-block semantic drift.

---

## 5. Topology Layer

Topology enters in two modes:

### Online mode
Cheap, stable, incremental:
- component counts,
- cycle indicators,
- signed coactivation summaries,
- lightweight filtrations,
- sketchable invariants.

### Offline mode
Expensive, exact, publishable:
- persistent homology,
- Mapper,
- multiscale graph summaries,
- intervention bifiltrations,
- comparison surfaces across schedules.

### `no_std` principle
The `no_std` kernel should provide:
- topological **types**,
- filtration **traits**,
- sketch **interfaces**,
- metric **contracts**,
- and minimal combinatorial primitives.

The heavy exact solvers live in `hm_std` or external engines.

That means:
- `persistent homology` in the core is a stub/trait contract,
- `Mapper` in the core is a stub/trait contract,
- exact execution is delegated to `std` crates or external libraries.

### Example kernel stub

```rust
pub trait PersistenceBackend {
    type Complex;
    type Diagram;
    type Error;

    fn compute_diagram(&self, complex: &Self::Complex) -> Result<Self::Diagram, Self::Error>;
}

pub trait MapperBackend {
    type Data;
    type Graph;
    type Error;

    fn compute_mapper(&self, data: &Self::Data) -> Result<Self::Graph, Self::Error>;
}
```

---

## 6. Signed Topological Sketches

The online sidecar stores **signed structure** rather than one undifferentiated graph.

Three channels are first-class:

- **positive**
- **negative**
- **cancellation**

This helps distinguish:
- supportive transport,
- suppressive transport,
- brittle compensatory behavior.

### Why this matters
A hybrid model can appear stable at the output while hiding unstable cancellation internally. Signed sketches make that visible.

### Sketch object

```rust
pub struct SignedSketch {
    pub positive_components: u32,
    pub negative_components: u32,
    pub cancellation_pairs: u32,
    pub cycle_hint: u32,
}
```

This is intentionally lightweight. Exact topology comes later.

---

## 7. Metrics

### Topological susceptibility
How quickly topology changes under intervention.

### Bridge dependence
How much explanatory or predictive flow must cross bridge regimes.

### Tract retention
How much behavior can be preserved inside local recurrent tracts alone.

### Gluing defect
How badly partial-sheaf sections fail to glue.

### Loop inconsistency / holonomy defect
How much transport around a closed path fails to return to the expected section/state.

### Replacement divergence
How much replacement-mode execution drifts from the native model.

---

## Python SDK API

## Primary user flow

```python
from hybrid_mechlab import HybridLab, profiles

lab = HybridLab.attach(
    model="Qwen/Qwen3.5-2B",
    profile=profiles.qwen35_dense_3_1(),
    mode="trace",
)

trace = lab.run(
    prompts=["Explain the proof sketch and track block transport."],
    capture=["codes", "sketches", "minimal_states"],
)

report = (
    trace
    .topology()
    .signed_sketches()
    .bridge_dependence()
)

print(report.summary())
```

## Core API surface

```python
class HybridLab:
    @classmethod
    def attach(cls, model, profile, mode="trace", **kwargs): ...
    def run(self, prompts, capture=None, interventions=None): ...
    def replace(self, replacement_policy): ...
    def export(self, path, format="parquet"): ...
    def topology(self): ...
    def compare(self, other_trace): ...
```

### Profiles

```python
profiles.qwen35_dense_3_1()
profiles.qwen35_dense_4_1_emulated()
profiles.olmo_hybrid_3_1()
profiles.kimi_linear_3_1()
profiles.custom(schedule=...)
```

### Interventions

```python
from hybrid_mechlab.hooks.interventions import FeatureClamp, BridgeGateScale

interventions = [
    FeatureClamp(target="block.4.post_recurrent_2", feature_id=731, value=0.0),
    BridgeGateScale(target="block.4.bridge", scale=0.25),
]
```

---

## Model Adapter Contract

Every supported model adapter must provide:

1. **schedule description**
2. **hook-point mapping**
3. **state extraction rules**
4. **bridge identification**
5. **optional replacement-mode hooks**

### Minimal Python adapter protocol

```python
class HybridAdapter(Protocol):
    name: str

    def schedule(self): ...
    def hook_points(self): ...
    def attach_hooks(self, model, capture_policy): ...
    def extract_state(self, raw_hook_output, hook_id): ...
    def bridge_mask(self): ...
```

### Adapter design rule
Adapters may know vendor/model specifics.  
The Rust core must never need to.

---

## Rust Core Design

## `hm_core` principles

- `#![no_std]`
- optional `alloc`
- fixed-capacity containers where practical
- explicit scalar abstraction
- deterministic IDs and codecs
- no hidden global state

### Core modules

#### `scalar.rs`
Numeric scalar traits:
- `f32`
- `f64`
- optional fixed-point
- deterministic conversions where possible

#### `sparse.rs`
Sparse feature containers:
- fixed-capacity sparse vectors,
- ragged sparse batches,
- sparse pair lists,
- index-sorted representations.

#### `schedule.rs`
Hybrid schedule representation:
- repeated motifs,
- custom schedules,
- block-operation semantics.

#### `transport.rs`
Transport operators:
- local state update relations,
- tract summaries,
- bridge crossings,
- compositional transport paths.

#### `connection.rs`
Connection-like abstractions:
- parallel transport proxies,
- discrete connection coefficients,
- loop composition,
- path compatibility.

#### `sheaf.rs`
Partial sheaf interfaces:
- local sections,
- restriction maps,
- gluing attempts,
- defect measures.

#### `graph.rs`, `hypergraph.rs`, `simplicial.rs`
Primitive combinatorial objects:
- typed nodes/edges,
- bounded hyperedges,
- simplex containers,
- filtration-ready views.

#### `filtrations.rs`
Filter values and multi-parameter scaffolding.

#### `topology.rs`, `mapper.rs`, `persistence.rs`
Traits and stubs for online and offline topology.

#### `sketches.rs`
Incremental signed summaries and compact topological sketches.

#### `ir.rs`
Core IR for trace objects and block/layer relations.

#### `codec.rs`
Deterministic binary and JSON-like canonical encoding helpers.

---

## BLT IR

The IR is multi-level.

### S-IR: Semantic IR
Human-meaningful model operations:

- `RecurrentTransportUpdate`
- `GlobalBridge`
- `FeedForward`
- `ResidualAdd`
- `Gate`
- `Norm`
- `SparseEncode`
- `SparseDecode`

### G-IR: Graph IR
Graph-structured execution view:
- nodes = hook states, codes, transport states
- edges = typed transitions

### T-IR: Topology IR
Optional lifted view for:
- filtrations,
- signed subcomplexes,
- Mapper covers,
- intervention axes.

### Why IR matters
Without an IR, every model family becomes a bespoke script.  
With an IR, the research stack becomes reusable.

---

## Trace Format

A trace is the canonical unit of work.

```python
trace = lab.run(...)
```

A trace contains:

- prompt metadata,
- model/profile identifiers,
- schedule identifier,
- hook captures,
- sparse codes,
- transport summaries,
- topology sketches,
- intervention metadata,
- reproducibility manifest,
- optional exact-state windows.

### Column schema (conceptual)

```text
trace_id
prompt_id
token_idx
block_id
layer_id
hook_id
regime_kind
schedule_local_index
feature_ids[]
feature_values[]
signed_sketch
transport_digest
intervention_id
model_hash
profile_hash
```

---

## Replacement-Model Mode

A core requirement is **replacement-mode semantics**.

This lets the researcher:
- swap native block behavior with sparse-code reconstructions,
- continue the forward pass,
- and quantify divergence.

### Why this matters
If the replacement path cannot preserve behavior, the interpretability object is too weak.

### Required replacement metrics

- logit divergence
- hidden-state divergence
- task-output divergence
- bridge-dependence under replacement
- topology drift under replacement

---

## Schedule-Agnostic Research Profiles

## 2:1 profile
Use for:
- more frequent global joins,
- lower tract isolation,
- studying dependence on bridge cadence.

## 3:1 profile
Default flagship:
- natural starting point for Qwen3.5-style hybrids.

## 4:1 profile
Use for:
- more aggressive tract emphasis,
- stronger local-memory hypothesis testing,
- bridge sparsity studies.

## Arbitrary schedules
Support things like:
- `2,2,1`
- `4,1,4,1`
- `7:1`
- irregular bridge spacing

because real research often starts where the canonical ratio breaks down.

---

## Research Questions the SDK Should Make Easy

- How does concept stability change as bridge cadence changes from 2:1 to 4:1?
- Which semantics remain local to recurrent tracts?
- Which semantics require periodic global bridges?
- Does a given feature family glue across blocks as a partial sheaf?
- Where do gluing failures cluster?
- What is the holonomy defect of a concept transported around a block loop?
- Do topology summaries stabilize across seeds?
- Is bridge use minimal or compensatory?
- Does replacement-mode success track topological stability?
- Can a block-level transcoder trained on one hybrid ratio transfer to another?

---

## Training Story

This repository does **not** require training a new base model.

It supports:

- training sparse encoders/decoders,
- training block-level transcoders,
- aligning codes across schedules,
- distilling topology-aware replacement layers,
- learning transport summaries.

### Suggested training tiers

#### Tier 1
Frozen base model, learned sparse encoder only.

#### Tier 2
Frozen base model, learned encoder + decoder replacement path.

#### Tier 3
Cross-ratio transfer:
- train on 3:1,
- evaluate on 2:1 / 4:1.

#### Tier 4
Cross-family transfer:
- Qwen3.5 → OLMo Hybrid → Kimi-style profiles.

---

## No-Std Boundary

The `no_std` core provides:
- type definitions,
- schedule semantics,
- compact sparse containers,
- transport/sheaf/connection traits,
- sketch contracts,
- deterministic hashing and codecs.

The `std` extension crates provide:
- filesystem IO,
- heavy graph builds,
- exact persistence engines,
- offline Mapper execution,
- Arrow/Parquet/Zarr.

### Rule
If something requires:
- filesystem access,
- parallel runtime,
- dynamic plugin loading,
- or heavy external dependencies,

it does **not** belong in `hm_core`.

---

## Binding Strategy

Use **PyO3 + maturin** for the primary Python bindings.

### Why PyO3
- standard Rust/Python path,
- manageable packaging,
- strong typed wrappers,
- suitable for research distribution.

### Binding design rule
Expose:
- stable value objects,
- batch operations,
- and manifest/report structs.

Do **not** expose unstable internal pointer-heavy APIs.

### Example binding objects
- `PyHybridSchedule`
- `PySparseCodeBatch`
- `PySignedSketch`
- `PyTransportDigest`
- `PyTraceHandle`
- `PyTopologyReport`

---

## Reproducibility and Audit

Even though this is a research SDK, the project should behave as if it may later support high-assurance workflows.

Every trace should record:
- model identifier,
- model hash when available,
- adapter/profile hash,
- schedule hash,
- hook policy hash,
- intervention manifest,
- Rust core version,
- Python package version,
- runtime seed,
- backend metadata.

### Why
Mechanistic claims that are not reproducible decay into screenshots.

---

## Suggested MVP

### Phase 0 — contracts
Ship:
- schedule IR,
- adapter interface,
- sparse code schema,
- signed sketch schema,
- trace manifest schema.

### Phase 1 — Qwen3.5 3:1 prototype
Ship:
- `qwen35.py` adapter,
- hook capture,
- sparse code path,
- signed sketch path,
- basic replacement mode,
- block maps and bridge-dependence metric.

### Phase 2 — ratio generalization
Ship:
- 2:1, 3:1, 4:1 schedule profiles,
- cross-ratio notebooks,
- topology comparison metrics.

### Phase 3 — partial sheaf + connection layer
Ship:
- partial sheaf contracts,
- gluing defect metrics,
- loop transport experiments,
- block-level concept transport.

### Phase 4 — offline exact topology
Ship:
- persistence backend interface,
- Mapper backend interface,
- publishable comparison notebooks.

---

## Example Python Usage

### Attach to a 3:1 profile

```python
from hybrid_mechlab import HybridLab, profiles

lab = HybridLab.attach(
    model="Qwen/Qwen3.5-2B",
    profile=profiles.qwen35_dense_3_1(),
    mode="trace",
    capture_policy="minimal",
)

trace = lab.run(
    prompts=["Track how the entity is preserved across block bridges."],
    capture=["codes", "sketches", "transport"],
)

print(trace.summary())
```

### Compare schedules

```python
lab_31 = HybridLab.attach(model="Qwen/Qwen3.5-2B", profile=profiles.qwen35_dense_3_1())
lab_41 = HybridLab.attach(model="Qwen/Qwen3.5-2B", profile=profiles.emulated_ratio(4, 1))

trace_31 = lab_31.run(prompts=["Analyze bridge cadence effects."])
trace_41 = lab_41.run(prompts=["Analyze bridge cadence effects."])

cmp = trace_31.compare(trace_41)
print(cmp.bridge_dependence_delta())
print(cmp.topological_susceptibility_delta())
```

### Partial sheaf experiment

```python
from hybrid_mechlab.topology.sheaf import build_partial_sheaf

ps = build_partial_sheaf(trace, basis="block_supernodes")
report = ps.gluing_report()
print(report.defect_score)
```

---

## Example Rust Kernel API

```rust
#![no_std]

pub mod schedule;
pub mod transport;
pub mod connection;
pub mod sheaf;
pub mod sketches;
pub mod topology;
pub mod persistence;
pub mod mapper;
```

### Example transport trait

```rust
pub trait Transport<State> {
    type Error;
    fn step(&self, from: &State) -> Result<State, Self::Error>;
}
```

### Example connection trait

```rust
pub trait DiscreteConnection<State> {
    type Path;
    type Error;

    fn transport_along(&self, state: &State, path: &Self::Path) -> Result<State, Self::Error>;
}
```

### Example gluing defect

```rust
pub struct GluingDefect {
    pub local_compatibility: f32,
    pub overlap_failure_mass: f32,
    pub unresolved_sections: u32,
}
```

---

## What the Initial README Must Promise

This repository should promise five things clearly:

1. **Reusable**
   - not trapped to one paper or one model family.
2. **Research-grade**
   - explicit contracts, typed manifests, reproducibility, ratio comparisons.
3. **Math-heavy**
   - transport, partial sheaves, connection, topology are design primitives.
4. **Python-friendly**
   - easy to use from notebooks and experiment scripts.
5. **Rust-disciplined**
   - small, stable, deterministic kernel.

---

## Risks and Mitigations

### Risk: too abstract
Mitigation:
- anchor everything in a real Qwen3.5 3:1 adapter first.

### Risk: topology becomes decorative
Mitigation:
- every topological object must correspond to a concrete experiment or metric.

### Risk: sheaf language outruns implementation
Mitigation:
- begin with partial sheaf contracts and defect scores, not maximal abstraction.

### Risk: `no_std` becomes a straightjacket
Mitigation:
- keep exact heavy machinery in companion `std` crates.

### Risk: replacement-mode quality is poor
Mitigation:
- treat replacement divergence as a first-class benchmark.

---

## Deliverables

### Repository artifacts
- one Python package,
- one Rust workspace,
- one flattened README/spec,
- one Qwen3.5 3:1 adapter,
- one ratio-general schedule module,
- one sparse-code trace format,
- one signed-sketch topology format.

### Demo artifacts
- notebook: attach + trace,
- notebook: block maps,
- notebook: bifiltration,
- notebook: ratio comparison,
- notebook: partial sheaf gluing report.

### Written artifacts
- BLT IR memo,
- topology sidecar memo,
- partial sheaf / connection memo.

---

## Build and Packaging

### Python
- `pyproject.toml`
- `maturin`
- optional extras:
  - `viz`
  - `offline-topology`
  - `dev`

### Rust
- workspace:
  - `hm_core`
  - `hm_std`
  - `hm_pyo3`

### CI
- rustfmt
- clippy
- mypy / pyright
- pytest
- round-trip trace tests
- deterministic codec tests

---

## Immediate Build Order

1. Create `hm_core` with:
   - IDs
   - sparse containers
   - schedule IR
   - sketch types
   - transport / sheaf / connection traits

2. Create `hm_pyo3` bindings for:
   - schedule
   - sparse batch
   - signed sketch
   - trace manifest

3. Create Python package with:
   - `HybridLab`
   - adapter base class
   - Qwen3.5 adapter
   - schedule helpers

4. Add BLT sparse encoder placeholder path.

5. Add topology online sketch wrappers.

6. Add first notebook.

---

## Productive Constraint

The most important design constraint is this:

> **The core math must remain useful even if the current flagship model family changes.**

That means:
- no Qwen-specific assumptions in the kernel,
- no hard-coded 3:1 semantics in the kernel,
- no Python-only core data contracts,
- no topology code that assumes a single feature geometry.

The repository should survive a change from:
- Qwen3.5
- to OLMo Hybrid
- to Kimi-style
- to a new custom hybrid family

without redesigning the mathematical substrate.

---

## Recommendation

Build this as a **Python SDK for hybrid-model research** with a **`no_std` Rust math kernel**, not as a one-off repo for a single paper.

The attached 3:1 BLT/TDA document should be treated as:
- the first profile,
- the first narrative,
- and the first README seed,

but the repository itself should be broader:

- **schedule-agnostic**
- **adapter-driven**
- **math-heavy**
- **replacement-model capable**
- **topology-aware**
- **partial-sheaf ready**
- **portable at the kernel layer**

That is the right shape for a reusable research platform.

---

## Selected External References

These references inform the initial profile and assumptions behind this repository:

- Qwen3.5-2B model card: hybrid 3:1 Gated DeltaNet / Gated Attention layout.
- Qwen3.5-9B model card: same scaffold at larger depth/width and long context.
- NVlabs GatedDeltaNet repository and paper.
- Lean proof validation documentation (`lean4checker`, `comparator`).
- Existing replacement-model / attribution-graph methodology.
- Persistent homology and Mapper literature.
- Hybrid-model examples such as OLMo Hybrid and Kimi Linear.

This repository should include those as bibliography entries in future `specs/` documents, but the flattened README keeps the emphasis on architecture and implementation rather than a formal citation apparatus.

---