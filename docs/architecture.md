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
| `ingestion/` | Parsers and preprocessors (Chapter 2) |
| `templates/` | Drain3 adapter, masking, template store (Chapter 3) |
| `evidence/` | Evidence graph abstraction (Chapter 4) |
| `providers/` | Deterministic and semantic evidence providers (Chapters 5, 10) |
| `inference/` | Event, entity, relationship, state inference (Chapter 6) |
| `export/` | Pydantic, JSON Schema, Mermaid, GraphML (Chapter 8) |
| `cli/` | Typer CLI (`ontolog`) (Chapters 1, 9) |

See [`.plans/IMPLEMENTATION_PLAN.md`](https://github.com/vadim-schultz/ontolog/blob/main/.plans/IMPLEMENTATION_PLAN.md)
for chapter-by-chapter deliverables and acceptance criteria.

## Benchmark corpora

Regression tests use small committed LogHub slices under `tests/fixtures/loghub/`. Larger corpora
are downloaded on demand into the gitignored `data/` directory. Ontolog does not train ML models on
logs — corpora support testing and benchmarking only.
