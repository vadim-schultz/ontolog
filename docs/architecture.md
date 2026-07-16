# Architecture

Ontolog is a **library-first** probabilistic domain-model inference engine. It is not a SIEM, log
viewer, or LLM wrapper.

## Pipeline (planned)

```text
Raw logs → Preprocessing → Drain3 templates → Evidence providers → Evidence graph
    → Inference engine → Probabilistic domain model → Export (Pydantic, JSON Schema, Mermaid, …)
```

## Core principles

* **Deterministic core first** — full pipeline works without any LLM
* **LLMs are optional evidence providers** — they enrich, never define truth
* **Templates are the semantic boundary** — Drain3 compresses raw logs before inference
* **Graph-native model** — generated code is a derived artifact
* **Human feedback is first-class evidence** — manual corrections dominate aggregation

## Package layout (`src/ontolog/`)

| Module | Responsibility |
|--------|----------------|
| `ingestion/` | Parsers, preprocessors, streaming reader (`ontolog ingest`) — see {doc}`ingestion` |
| `templates/` | Drain3 adapter, masking, template store (`ontolog templates`) — see {doc}`templates` |
| `storage/` | SQLite persistence for templates and occurrences |
| `evidence/` | Evidence graph (`EvidenceGraph`, `load_evidence_graph`) — see {doc}`api` |
| `providers/` | Deterministic and semantic evidence providers (Chapters 5, 10) |
| `inference/` | Event, entity, relationship, state inference (Chapter 6) |
| `export/` | Pydantic, JSON Schema, Mermaid, GraphML (Chapter 8) |
| `cli/` | Typer CLI (`ontolog`) — thin wrappers over library APIs |

See [`.plans/IMPLEMENTATION_PLAN.md`](https://github.com/vadim-schultz/ontolog/blob/main/.plans/IMPLEMENTATION_PLAN.md)
for chapter-by-chapter deliverables and acceptance criteria.

## Benchmark corpora

Regression tests use small committed LogHub slices under `tests/fixtures/loghub/`. Larger corpora
are downloaded on demand into the gitignored `data/` directory. Ontolog does not train ML models on
logs — corpora support testing and benchmarking only.
