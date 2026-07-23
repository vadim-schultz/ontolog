# Changelog

## Unreleased

### Changed

* **BREAKING:** `InferOutput` gains a required `graph: EvidenceGraph` field
* Exporters are now frozen dataclasses composed with an injected `renderer` (no change to
  `export_domain_model()`/`export_with_graph()` call signatures)
* **BREAKING:** Public CLI collapsed to `ontolog infer PATH --format EXPORT` only; removed
  `ingest`, `templates`, `export`, and `graph` commands
* **BREAKING:** `ontolog.infer()` now requires `format` (export format) and returns `InferOutput`
  with `.model` and `.artifact`; removed `store_path` and `fresh` parameters
* **BREAKING:** `--format` on the CLI now selects export format; input log format is `--log-format`
* Each infer run uses an ephemeral in-memory store (no `--store` or `--fresh`)

### Added

* Export layer (Chapter 8): `export_domain_model()`, core exporters (Pydantic, JSON Schema,
  Mermaid, Markdown, GraphML), plus `domain-json`, `evidence-graph`, and `full` formats
* `GraphExporter` Protocol, `Renderer`/`JsonRenderer`/`GraphmlRenderer`/`Jinja2Renderer`
* `EvidenceGraph.to_payload()`, `InferenceContext`, `build_inference_context_from_store()`,
  `build_domain_model_with_graph_from_store()`
* `jinja2` dependency; Markdown and Mermaid exporters use packaged Jinja2 templates
* `Exporter` Protocol, `ExportFormat`, `ExportOptions`, and `export_view()` filtering
* `ontolog export <format> --store PATH` CLI with `--all` and `--provenance` flags
* `jsonschema` added to `[dev]` optional dependencies for schema validation tests
* Probabilistic aggregation (Chapter 7): `ProbabilisticDomainModel`, tier-weighted
  `aggregate_inference_result()`, and `build_domain_model()` pipeline entry point
* `EvidenceSourceTier`, `EvidenceSourceWeights` on `OntologConfig` (human > deterministic > LLM)
* Domain types: `Entity`, `Event`, `Field`, `Relationship`, `StateMachine` with full provenance
* Inference engine (Chapter 6): entity, event, field, relationship, and state-machine
  candidates via `build_inference_result()` and `run_inference()`
* Deterministic evidence providers: regex, statistics, co-occurrence, namespace, temporal, process
* `EvidenceProvider` Protocol, `provider_registry()`, and `run_providers()` orchestrator
* `EvidenceFinding`, `ProviderInput`, and `ProviderConfig` / `ProviderKind` configuration
* Shared regex patterns in `templates/patterns.py`; `SqliteTemplateStore.list_occurrences()`
* `load_evidence_graph(store_path, config=...)` populates graph from stored templates
* Fixtures: `order_cooccurrence.log`, `order_lifecycle.log`
* Evidence graph foundation: `Evidence`, `Node`, `Edge`, `NodeKind` models
* `EvidenceGraph` (NetworkX-backed) with JSON serialization and evidence attachment
* `load_evidence_graph()` library API for loading graphs from the SQLite store
* `ontolog graph --show` CLI (thin wrapper over library API)
* CLI reorganized into per-command sub-packages (`cli/ingest`, `cli/templates`, `cli/graph`)
* Template extraction via Drain3 (`TemplateExtractor`, `extract_templates`)
* Configurable masking (IP, UUID, MAC, hex, email, numbers, timestamps)
* `Template` model and SQLite persistence (`templates`, `template_occurrences`)
* `ontolog templates` CLI with Rich summary table
* Log ingestion: syslog, JSONL, and plain parsers
* Preprocessor registry and streaming reader (file, directory, stdin)
* `ontolog ingest` CLI command (JSONL output)
* Fixtures: `controlboard.log`, LogHub `apache_2k` / `openssh_2k` slices
* `LogRecord` model, `OntologConfig`, typed exceptions
* `ontolog` CLI with `--version` and `--help`
* Project scaffold (Chapter 0): `src/ontolog` package, pytest harness, Sphinx docs stub, GitHub
  Actions CI (ruff, mypy, pytest, docs build, wheel smoke test), Read the Docs config,
  pre-commit hooks, and unified implementation plan.

## 0.0.1 — 2026-07-14

### Added

* Initial package skeleton and engineering baseline.
