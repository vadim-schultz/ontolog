# Export formats

Chapter 8 turns a `ProbabilisticDomainModel` into derived artifacts for developers.
The domain model remains the source of truth; exports are filtered views of that model.

## Library API

```python
from pathlib import Path

from ontolog.config import default_config
from ontolog.export import ExportFormat, ExportOptions, export_domain_model
from ontolog.inference import build_domain_model

model = build_domain_model(Path("ontolog.db"), config=default_config())
source = export_domain_model(model, ExportFormat.PYDANTIC)
schema = export_domain_model(model, ExportFormat.JSON_SCHEMA)
```

### `ExportOptions`

| Field | Default | Description |
|-------|---------|-------------|
| `include_ineligible` | `False` | Include claims below `ConfidenceThresholds.export` |
| `include_provenance` | `False` | Include evidence sources in Markdown reports |

## CLI

```bash
# Extract templates into a store (prerequisite)
ontolog templates tests/fixtures/controlboard.log --store ontolog.db

# Export formats
ontolog export pydantic --store ontolog.db
ontolog export json-schema --store ontolog.db
ontolog export mermaid --store ontolog.db
ontolog export markdown --store ontolog.db
ontolog export graphml --store ontolog.db

# Include ineligible claims
ontolog export markdown --store ontolog.db --all

# Neo4j bulk-import CSV (requires pip install ontolog[graph])
ontolog export neo4j-csv --store ontolog.db --output-dir ./neo4j-import
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
