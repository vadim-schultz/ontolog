# Export formats

Chapter 8 turns a `ProbabilisticDomainModel` into derived artifacts for developers.
The domain model remains the source of truth; exports are filtered views of that model.

## Library API

```python
from ontolog import infer

output = infer("tests/fixtures/controlboard.log", format="mermaid")
print(output.artifact)
print(len(output.model.entities))
```

Pass `ExportOptions` for filtering:

```python
from ontolog import infer
from ontolog.export import ExportOptions

output = infer(
    "app.log",
    format="markdown",
    export_options=ExportOptions(include_ineligible=True, include_provenance=True),
)
```

### Debugging: export an existing model

```python
from ontolog.export import ExportFormat, export_domain_model
from ontolog.inference.builder import build_domain_model_from_store
from ontolog.storage import SqliteTemplateStore

with SqliteTemplateStore("ontolog.db") as store:
    model = build_domain_model_from_store(store)
source = export_domain_model(model, ExportFormat.PYDANTIC)
```

### `ExportOptions`

| Field | Default | Description |
|-------|---------|-------------|
| `include_ineligible` | `False` | Include claims below `ConfidenceThresholds.export` |
| `include_provenance` | `False` | Include evidence sources in Markdown reports |

## CLI

```bash
ontolog infer tests/fixtures/controlboard.log --format mermaid
ontolog infer tests/fixtures/controlboard.log --format pydantic
ontolog infer tests/fixtures/controlboard.log --format json-schema
ontolog infer tests/fixtures/controlboard.log --format markdown
ontolog infer tests/fixtures/controlboard.log --format graphml

# Include ineligible claims
ontolog infer tests/fixtures/controlboard.log --format markdown --all

# Neo4j bulk-import CSV (requires pip install ontolog[graph])
ontolog infer tests/fixtures/controlboard.log --format neo4j-csv --output-dir ./neo4j-import
```

## Formats

### Pydantic (`pydantic`)

Generates importable Python source with one `BaseModel` per export-eligible entity and a
`DomainFields` model for typed log fields. Generated code is validated in tests with `ruff` and
`mypy`.

### JSON Schema (`json-schema`)

Emits Draft 2020-12 JSON with entity definitions and typed field properties. Inferred type slugs
(`ipv4`, `hex`, `uuid`, …) map to JSON Schema formats and patterns via `export/type_map.py`.

### Mermaid (`mermaid`)

Produces `erDiagram` blocks for entities and relationships, plus `stateDiagram-v2` blocks for
export-eligible state machines.

### Markdown (`markdown`)

Human-readable report with confidence percentages per section (entities, events, fields,
relationships, state machines). Use `--provenance` on the CLI to include evidence sources.

### GraphML (`graphml`)

NetworkX-backed GraphML XML with nodes for entities, events, and fields, and edges for
relationships.

### Neo4j CSV (`neo4j-csv`)

Optional format behind the `[graph]` extra. Writes `nodes.csv` and `relationships.csv` suitable
for Neo4j bulk import. No Neo4j driver is required.

## Confidence filtering

During aggregation, each claim receives `export_eligible` when its confidence meets
`ConfidenceThresholds.export` (default `0.7`). Exporters call `export_view()` to filter collections
before rendering unless `include_ineligible=True`.
