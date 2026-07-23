# Architecture

Ontolog is a **library-first** probabilistic domain-model inference engine. It is not a SIEM, log
viewer, or LLM wrapper.

## Pipeline

```text
Raw logs → Preprocessing → Drain3 templates → Evidence providers → Evidence graph
    → Inference engine → Probabilistic domain model → Export (Pydantic, JSON Schema, Mermaid, …)
```

## Evidence providers (Chapter 5)

Deterministic providers analyze stored templates and occurrences, then populate an
`EvidenceGraph` with nodes, edges, and provenance-backed scores:

| Provider | Signals |
|----------|---------|
| `NamespaceProvider` | Process name → entities; template prefix → events; parameters → fields |
| `RegexProvider` | IPv4, hex, UUID, MAC, email, URL, path, timestamp patterns on parameter values |
| `StatisticsProvider` | Frequency, cardinality, entropy |
| `CoOccurrenceProvider` | Parameters appearing together in the same occurrence |
| `TemporalProvider` | Ordered template sequences by timestamp |
| `ProcessProvider` | Repeated template subsequences (activity patterns) |

Enable or disable providers via `ProviderConfig` on `OntologConfig`. The orchestrator
`run_providers()` applies findings in a fixed order. `load_evidence_graph(store_path, config=...)`
loads templates and occurrences from SQLite and runs the enabled providers.

## Inference engine (Chapter 6)

Inference passes read the populated evidence graph and promote nodes/edges into structured
candidates (`EntityCandidate`, `EventCandidate`, `FieldCandidate`, `RelationshipCandidate`,
`StateMachineCandidate`) bundled in an `InferenceResult`:

| Pass | Signals |
|------|---------|
| `EntityInferencePass` | Process entities; noun-phrase entities from field labels (e.g. `interface` → Interface) |
| `EventInferencePass` | Template-prefix events with verb lexicon (send, receive, connect, create, …) |
| `FieldInferencePass` | Parameter types from `has_type` edges; semantic names via `destination=<IP>` mapping |
| `RelationshipInferencePass` | `owns` from `has_field` edges linking entities to structural fields |
| `StateInferencePass` | Lifecycle transitions from status values and temporal `follows` edges |

Enable or disable passes via `InferenceConfig`. `build_inference_result(store_path, config=...)`
runs providers then inference in a fixed order.

## Probabilistic aggregation (Chapter 7)

Aggregation merges inference candidates into a canonical `ProbabilisticDomainModel` with
full provenance and export eligibility:

| Component | Role |
|-----------|------|
| `ProbabilisticDomainModel` | Frozen domain model (`Entity`, `Event`, `Field`, `Relationship`, `StateMachine`) |
| `aggregate_inference_result()` | Tier-weighted merge with ranked alternatives |
| `EvidenceSourceWeights` | Per-tier multipliers (`human` > `deterministic` > `LLM`) |
| `build_domain_model()` | Full pipeline: providers → inference → aggregation |

Conflicting evidence resolves by tier priority (human suppresses lower tiers), then weighted
confidence within the winning tier. Each claim carries `confidence`, `evidence`, and
`export_eligible` (from `ConfidenceThresholds.export`).

## Export layer (Chapter 8)

The export layer turns a `ProbabilisticDomainModel` into developer-facing artifacts. By default,
only claims with `export_eligible=True` are included; pass `ExportOptions(include_ineligible=True)`
or `ExportOptions(include_ineligible=True)` or `ontolog infer --all` for the full model.

| Format | Module | Output |
|--------|--------|--------|
| Pydantic | `export/pydantic_gen.py` | Importable Python `BaseModel` source |
| JSON Schema | `export/json_schema.py` | Draft 2020-12 schema JSON |
| Mermaid | `export/mermaid.py` | ER diagram + state-transition diagrams |
| Markdown | `export/markdown_report.py` | Human-readable summary |
| GraphML | `export/graphml.py` | XML graph for NetworkX-compatible tools |
| Neo4j CSV | `export/graphml.py` | Bulk-import CSV (requires `[graph]` extra) |

`export_domain_model(model, format, options=...)` is the library entry point for exporting an
existing model. The public path is `ontolog.infer(source, format=...)`, which runs the full
pipeline and returns an `InferOutput` with `.model` and `.artifact`.

## Core principles

* **Deterministic core first** — full pipeline works without any LLM
* **LLMs are optional evidence providers** — they enrich, never define truth
* **Templates are the semantic boundary** — Drain3 compresses raw logs before inference
* **Graph-native model** — generated code is a derived artifact
* **Human feedback is first-class evidence** — manual corrections dominate aggregation

## Package layout (`src/ontolog/`)

| Module | Responsibility |
|--------|----------------|
| `ingestion/` | Parsers, preprocessors, streaming reader — see {doc}`ingestion` |
| `templates/` | Drain3 adapter, masking, template store — see {doc}`templates` |
| `storage/` | SQLite persistence for templates and occurrences |
| `evidence/` | Evidence graph (`EvidenceGraph`, `load_evidence_graph`, `run_providers`) — see {doc}`api` |
| `providers/` | Deterministic evidence providers (Chapter 5); semantic providers (Chapter 10) |
| `inference/` | Event, entity, relationship, state inference (Chapter 6); aggregation (Chapter 7) |
| `export/` | Pydantic, JSON Schema, Mermaid, GraphML export (Chapter 8) — see {doc}`export` |
| `cli/` | Typer CLI (`ontolog`) — thin wrappers over library APIs |

See [`.plans/IMPLEMENTATION_PLAN.md`](https://github.com/vadim-schultz/ontolog/blob/main/.plans/IMPLEMENTATION_PLAN.md)
for chapter-by-chapter deliverables and acceptance criteria.

## Benchmark corpora

Regression tests use small committed LogHub slices under `tests/fixtures/loghub/`. Larger corpora
are downloaded on demand into the gitignored `data/` directory. Ontolog does not train ML models on
logs — corpora support testing and benchmarking only.
