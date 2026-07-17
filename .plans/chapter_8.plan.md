---
name: Ontolog Chapter 8
overview: Chapter 8 adds export layer — Pydantic, JSON Schema, Mermaid, Markdown, GraphML/Neo4j CSV exporters with export_eligible filtering and ontolog export CLI.
status: complete
---

# Chapter 8 — Export layer

**Status:** Complete on branch `feat/ch8-export-layer`

## Delivered

| Deliverable | Location |
|-------------|----------|
| Export options | `src/ontolog/export/options.py` |
| Type mapping | `src/ontolog/export/type_map.py` |
| View filter | `src/ontolog/export/view.py` |
| Format registry | `src/ontolog/export/registry.py`, `formats.py` |
| Pydantic codegen | `src/ontolog/export/pydantic_gen.py` |
| JSON Schema | `src/ontolog/export/json_schema.py` |
| Mermaid | `src/ontolog/export/mermaid.py` |
| Markdown report | `src/ontolog/export/markdown_report.py` |
| GraphML + Neo4j CSV | `src/ontolog/export/graphml.py` |
| `Exporter` Protocol | `src/ontolog/types.py` |
| CLI | `src/ontolog/cli/export/commands.py` |
| `[graph]` extra | `pyproject.toml` |

## Tests

- `tests/unit/test_export_type_map.py`
- `tests/unit/test_export_filter.py`
- `tests/unit/test_export_json_schema.py`
- `tests/unit/test_export_pydantic_gen.py`
- `tests/unit/test_export_mermaid.py`
- `tests/unit/test_export_markdown.py`
- `tests/unit/test_export_graphml.py`
- `tests/unit/test_cli_export.py`
- `export_fixture()` helper in `tests/helpers.py`

## Acceptance criteria

- [x] `Exporter` Protocol + factory for five core formats
- [x] Default exports respect `export_eligible` / `ConfidenceThresholds.export`
- [x] `ontolog export pydantic` emits importable code passing `ruff` + `mypy`
- [x] Mermaid ER output for controlboard fixture (entities + `owns` relationship)
- [x] Mermaid state diagram for order_lifecycle fixture
- [x] JSON Schema validates sample instance (`jsonschema` in dev deps)
- [x] GraphML is well-formed XML with relationship edges
- [x] Neo4j CSV behind `[graph]` extra registration
- [x] `ruff check`, `mypy src`, `pytest` green
