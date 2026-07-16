---
name: Ontolog Chapter 4
overview: Chapter 4 introduces the evidence graph foundation — frozen Pydantic models (Evidence, Node, Edge, NodeKind), a mutable EvidenceGraph service wrapping NetworkX, lossless JSON serialization, load_evidence_graph library API, and a thin ontolog graph --show CLI wrapper — implemented via six red-green-refactor TDD cycles following chapter_3.plan.md conventions.
todos:
  - id: prereq-networkx
    content: Add networkx>=3.0 to pyproject.toml (+ mypy override if needed)
    status: pending
  - id: tdd-cycle-1
    content: "RED→GREEN→REFACTOR: Evidence + NodeKind (test_evidence_model.py → models/evidence.py)"
    status: pending
  - id: tdd-cycle-2
    content: "RED→GREEN→REFACTOR: Node + Edge models (extend test_evidence_model.py)"
    status: pending
  - id: tdd-cycle-3
    content: "RED→GREEN→REFACTOR: EvidenceGraph add/query (test_evidence_graph.py → evidence/graph.py)"
    status: pending
  - id: tdd-cycle-4
    content: "RED→GREEN→REFACTOR: attach_evidence + to_json/from_json round-trip"
    status: pending
  - id: tdd-cycle-5
    content: "RED→GREEN→REFACTOR: Graph loader library API (test_evidence_loader.py → evidence/loader.py)"
    status: pending
  - id: tdd-cycle-6
    content: "RED→GREEN→REFACTOR: CLI sub-package layout + thin graph wrapper (test_cli_graph.py → cli/graph/)"
    status: pending
  - id: docs-changelog
    content: Update docs/api.md, architecture.md, CHANGELOG.md, .plans/README.md
    status: pending
isProject: false
---

# Chapter 4 — Evidence graph foundation

**Artifact path:** [`.plans/chapter_4.plan.md`](file:///home/schult_v/projects/ontolog/.plans/chapter_4.plan.md) (update [`.plans/README.md`](file:///home/schult_v/projects/ontolog/.plans/README.md) on completion)

## TDD methodology

Every capability follows **red → green → refactor** (same as [chapter_3.plan.md](file:///home/schult_v/projects/ontolog/.plans/chapter_3.plan.md)):

1. **Red** — write tests asserting behavior; run `pytest <test_file> -x` and confirm meaningful failure (`ModuleNotFoundError` / `ImportError` / missing behavior)
2. **Green** — smallest production change to pass
3. **Refactor** — clean up; re-run narrow test file, then full gate

```bash
pytest tests/unit/test_evidence_model.py -x   # per cycle
ruff check src tests && ruff format --check src tests && mypy src && pytest
```

---

## Starting point (Chapter 3 complete)

| Area | Status |
|------|--------|
| [`LogRecord`](file:///home/schult_v/projects/ontolog/src/ontolog/models/log_record.py) / [`Template`](file:///home/schult_v/projects/ontolog/src/ontolog/models/template.py) | Frozen Pydantic value objects with JSON round-trip tests |
| [`SqliteTemplateStore`](file:///home/schult_v/projects/ontolog/src/ontolog/storage/sqlite.py) | Templates only — **no graph tables** |
| [`TemplateExtractor`](file:///home/schult_v/projects/ontolog/src/ontolog/templates/extractor.py) | Mutable `@dataclass` service pattern |
| CLI | `ingest`, `templates` — no `graph` command |
| `networkx` | **Not in** [`pyproject.toml`](file:///home/schult_v/projects/ontolog/pyproject.toml) yet (listed in unified plan core deps) |
| Evidence code | **None** — greenfield |

---

## Goal

Central graph abstraction for all downstream inference (Ch5 providers → Ch6 inference → Ch7 aggregation).

```mermaid
flowchart TD
    templates[TemplateStore] --> graphCmd[ontolog_graph_show_stub]
  graphCmd --> emptyGraph[EvidenceGraph_in_memory]
    providers[Ch5_EvidenceProviders] -.-> graph[EvidenceGraph]
    graph --> inference[Ch6_Inference]
    node[Node_with_evidence] --> graph
    edge[Edge_with_evidence] --> graph
```

Ch4 builds the graph **container and models only** — providers populate it in Ch5.

**Library-first rule:** Ontolog is a library; the CLI is a thin adapter. All graph behavior (load, inspect, serialize) lives under `src/ontolog/evidence/` and is importable as Python API. CLI commands parse arguments, call library functions, and render output — no business logic in `cli/`.

```python
# Python API (Ch4)
from ontolog.evidence import EvidenceGraph, load_evidence_graph

graph = load_evidence_graph(Path("ontolog.db"))
print(graph.node_count(), graph.edge_count())
```

---

## OOP / design conventions

| Layer | Pattern | Ch4 application |
|-------|---------|-----------------|
| Domain values | Frozen Pydantic `BaseModel` | `Evidence`, `Node`, `Edge` |
| Closed enums | `StrEnum` | `NodeKind` (like [`MaskKind`](file:///home/schult_v/projects/ontolog/src/ontolog/config.py)) |
| Services | Mutable class (not frozen dataclass) | `EvidenceGraph` owns internal `nx.DiGraph` |
| Errors | `OntologError` subclass with context | Reuse [`InferenceError`](file:///home/schult_v/projects/ontolog/src/ontolog/errors.py) for missing nodes/edges, duplicate IDs |
| Model JSON | Pydantic `model_dump_json` / `model_validate_json` only | Per-model round-trip in tests |
| Graph JSON | Custom `to_json()` / `from_json()` on service | Composite document — not a Pydantic model |
| Private helpers | Module-level `_encode_*` / `_merge_*` | Graph (de)serialization helpers in `evidence/graph.py` |
| Library API | Module-level functions + service classes (like [`extract_templates`](file:///home/schult_v/projects/ontolog/src/ontolog/templates/extractor.py)) | `load_evidence_graph()` in `evidence/loader.py` — store I/O and graph assembly |
| CLI | One sub-package per command; **thin wrapper only** | Parse args → call library → `echo_status` / Rich render; no store or graph logic |

**Immutability rule:** `Node` and `Edge` are frozen; `attach_evidence` replaces them via `model_copy(update={...})` rather than mutating in place.

---

## Prerequisite — add `networkx` dependency

Before TDD Cycle 1 (or at latest before Cycle 3):

```toml
# pyproject.toml [project] dependencies
"networkx>=3.0",
```

Add mypy override if needed:

```toml
[[tool.mypy.overrides]]
module = ["networkx", "networkx.*"]
ignore_missing_imports = true
```

---

## TDD Cycle 1 — Evidence model + NodeKind

### Red: `tests/unit/test_evidence_model.py` (Evidence + NodeKind section)

| Test | Asserts |
|------|---------|
| `test_evidence_construct_minimal` | `source`, `score`, `explanation` required; `samples` defaults to `()` |
| `test_evidence_score_bounds` | `score=1.5` and `score=-0.1` raise `ValidationError` |
| `test_evidence_construct_full` | `samples=("line1", "line2")` preserved |
| `test_evidence_frozen` | Mutation raises |
| `test_evidence_json_round_trip` | `model_dump_json` / `model_validate_json` |
| `test_node_kind_values` | All six kinds: `ENTITY`, `FIELD`, `EVENT`, `TYPE`, `STATE`, `RELATIONSHIP` |
| `test_node_kind_str_enum` | `NodeKind.ENTITY == "entity"` (lowercase values, uppercase names — match `MaskKind` style) |

**Expected failure:** `ModuleNotFoundError: ontolog.models.evidence`

### Green: `src/ontolog/models/evidence.py`

```python
class NodeKind(StrEnum):
    ENTITY = "entity"
    FIELD = "field"
    EVENT = "event"
    TYPE = "type"
    STATE = "state"
    RELATIONSHIP = "relationship"

class Evidence(BaseModel):
    model_config = ConfigDict(frozen=True)
    source: str
    score: Annotated[float, Field(ge=0.0, le=1.0)]
    explanation: str
    samples: tuple[str, ...] = ()
```

Export from [`models/__init__.py`](file:///home/schult_v/projects/ontolog/src/ontolog/models/__init__.py).

### Refactor

- Match [`template.py`](file:///home/schult_v/projects/ontolog/src/ontolog/models/template.py) docstring style
- Add ruff per-file ignore for `TC003` on new model file

---

## TDD Cycle 2 — Node and Edge models

### Red: extend `tests/unit/test_evidence_model.py`

| Test | Asserts |
|------|---------|
| `test_node_construct_minimal` | `id`, `kind`, `label`; empty `evidence` |
| `test_node_construct_with_evidence` | `evidence` tuple of `Evidence` |
| `test_node_frozen` | Mutation raises |
| `test_node_json_round_trip` | Includes nested `Evidence` list |
| `test_edge_construct_minimal` | `source_id`, `target_id`; optional `label=None` |
| `test_edge_construct_with_evidence` | Evidence attached |
| `test_edge_frozen` | Mutation raises |
| `test_edge_json_round_trip` | Lossless |

### Green: add to `models/evidence.py`

```python
class Node(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    kind: NodeKind
    label: str
    evidence: tuple[Evidence, ...] = ()

class Edge(BaseModel):
    model_config = ConfigDict(frozen=True)
    source_id: str
    target_id: str
    label: str | None = None
    evidence: tuple[Evidence, ...] = ()
```

Update `models/__init__.py` exports: `Evidence`, `Node`, `Edge`, `NodeKind`.

---

## TDD Cycle 3 — EvidenceGraph add/query

### Red: `tests/unit/test_evidence_graph.py`

| Test | Asserts |
|------|---------|
| `test_empty_graph_counts` | `node_count() == 0`, `edge_count() == 0` |
| `test_add_node_and_get` | `add_node` then `get_node(id)` returns equal `Node` |
| `test_add_edge_and_get` | `add_edge` after two nodes; `get_edge(src, tgt)` returns `Edge` |
| `test_add_node_duplicate_raises` | Second `add_node` same `id` → `InferenceError` |
| `test_add_edge_missing_endpoint_raises` | Edge without nodes → `InferenceError` |
| `test_nodes_and_edges_lists` | `nodes()` / `edges()` return all added items (order not asserted) |
| `test_underlying_networkx_graph` | `graph.nx_graph` is `nx.DiGraph` with matching node/edge counts (exposes read-only property for Ch6) |

**Expected failure:** `ImportError: ontolog.evidence.graph`

### Green: `src/ontolog/evidence/graph.py`

```python
class EvidenceGraph:
    def __init__(self) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()

    @property
    def nx_graph(self) -> nx.DiGraph:
        return self._graph

    def add_node(self, node: Node) -> None: ...
    def add_edge(self, edge: Edge) -> None: ...
    def get_node(self, node_id: str) -> Node | None: ...
    def get_edge(self, source_id: str, target_id: str) -> Edge | None: ...
    def nodes(self) -> list[Node]: ...
    def edges(self) -> list[Edge]: ...
    def node_count(self) -> int: ...
    def edge_count(self) -> int: ...
```

**Storage strategy:** Store serialized `Node` / `Edge` as `model_dump(mode="json")` in NetworkX node attribute `"data"` and edge attribute `"data"`. Single source of truth in NetworkX — no parallel dict.

Create [`evidence/__init__.py`](file:///home/schult_v/projects/ontolog/src/ontolog/evidence/__init__.py) exporting `EvidenceGraph`.

### Refactor

- Extract `_node_from_attrs` / `_edge_from_attrs` private helpers
- `add_edge` rejects duplicate `(source_id, target_id)` with `InferenceError`

---

## TDD Cycle 4 — Evidence attachment + JSON serialization

### Red: extend `tests/unit/test_evidence_graph.py`

| Test | Asserts |
|------|---------|
| `test_attach_evidence_to_node` | Appends to `node.evidence`; prior evidence preserved |
| `test_attach_evidence_to_node_missing_raises` | Unknown `node_id` → `InferenceError` |
| `test_attach_evidence_to_edge` | Appends to `edge.evidence` |
| `test_attach_evidence_to_edge_missing_raises` | Unknown edge → `InferenceError` |
| `test_json_round_trip_empty` | `from_json(graph.to_json())` equal counts |
| `test_json_round_trip_populated` | Build graph with 2 nodes, 1 edge, evidence on both; round-trip equals via `nodes()`/`edges()` set comparison |
| `test_json_round_trip_preserves_evidence_order` | Multiple evidence entries keep order |

Use a helper fixture:

```python
@pytest.fixture
def sample_evidence() -> Evidence:
    return Evidence(source="regex", score=0.95, explanation="IPv4 pattern", samples=("192.168.1.1",))
```

### Green: add to `EvidenceGraph`

```python
def attach_evidence_to_node(self, node_id: str, evidence: Evidence) -> None: ...
def attach_evidence_to_edge(self, source_id: str, target_id: str, evidence: Evidence) -> None: ...
def to_json(self, *, indent: int | None = 2) -> str: ...
@classmethod
def from_json(cls, data: str) -> EvidenceGraph: ...
```

**JSON document schema (versioned):**

```json
{
  "version": 1,
  "nodes": [ { "id": "...", "kind": "entity", "label": "...", "evidence": [...] } ],
  "edges": [ { "source_id": "...", "target_id": "...", "label": null, "evidence": [...] } ]
}
```

- Parse with `Node.model_validate` / `Edge.model_validate` per entry
- `from_json` rebuilds via `add_node` / `add_edge` then re-attaches evidence (or constructs with evidence inline — simpler: allow `add_node` to accept nodes that already carry evidence)
- Unknown `version` → `InferenceError`

### Refactor

- Add `__eq__` helper or test utility `graphs_equal(a, b)` comparing sorted nodes/edges (for round-trip tests only — do not add `__eq__` on `EvidenceGraph` unless tests need it)

---

## TDD Cycle 5 — Graph loader (library API)

All store interaction and graph assembly belongs in the library, not the CLI. Mirror the [`extract_templates()`](file:///home/schult_v/projects/ontolog/src/ontolog/templates/extractor.py) pattern: a module-level function orchestrating store + service.

### Red: `tests/unit/test_evidence_loader.py`

| Test | Asserts |
|------|---------|
| `test_load_returns_empty_graph` | Fresh/valid store → `EvidenceGraph` with zero nodes/edges (Ch4 stub) |
| `test_load_opens_store_at_path` | Callable with `Path`; does not require caller to manage store lifecycle |
| `test_load_invalid_path_raises_storage_error` | Missing/unopenable DB → `StorageError` |
| `test_load_after_templates_still_empty` | Store populated by `SqliteTemplateStore.upsert_template` still returns empty graph until graph persistence lands |

**Expected failure:** `ImportError: ontolog.evidence.loader`

### Green: `src/ontolog/evidence/loader.py`

```python
def load_evidence_graph(store_path: Path) -> EvidenceGraph:
    """Load the evidence graph from the Ontolog SQLite store.

    Ch4 stub: validates the store opens and returns an empty in-memory graph.
    Graph persistence and provider population arrive in later chapters.
    """
    store = SqliteTemplateStore(store_path)
    try:
        store.list_templates()  # ensure schema is reachable
        return EvidenceGraph()
    finally:
        store.close()
```

Export `load_evidence_graph` from [`evidence/__init__.py`](file:///home/schult_v/projects/ontolog/src/ontolog/evidence/__init__.py) alongside `EvidenceGraph`.

### Refactor

- Keep loader free of CLI imports (`rich`, `typer`)
- Future chapters extend this function (load persisted graph, run providers) without touching CLI

---

## TDD Cycle 6 — CLI sub-package layout + thin graph wrapper

### CLI architecture (one sub-package per command)

Refactor the flat [`cli/main.py`](file:///home/schult_v/projects/ontolog/src/ontolog/cli/main.py) into a **thin registry** matching [`rsb_test_storage_client/cli`](file:///home/schult_v/projects/rsb-test-storage-client/src/rsb_test_storage_client/cli/main.py):

```text
cli/
├── __init__.py              # export app
├── main.py                  # root Typer + add_typer registrations only
├── logging.py               # unchanged
├── output.py                # shared render helpers
├── ingest/
│   ├── __init__.py          # export ingest_app
│   └── commands.py          # moved from main.py
├── templates/
│   ├── __init__.py          # export templates_app
│   └── commands.py          # moved from main.py
└── graph/
    ├── __init__.py          # export graph_app
    └── commands.py          # NEW — graph --show stub
```

**`main.py` stays lightweight** (~30 lines): root callback (`--version`, `setup_cli_logging`) plus registrations:

```python
from ontolog.cli.graph import graph_app
from ontolog.cli.ingest import ingest_app
from ontolog.cli.templates import templates_app

app = typer.Typer(name="ontolog", help="...", no_args_is_help=True, add_completion=False)

app.add_typer(ingest_app, name="ingest")
app.add_typer(templates_app, name="templates")
app.add_typer(graph_app, name="graph")
```

**Per-command sub-package pattern** — each `commands.py` delegates to the library:

```python
# cli/graph/commands.py
from ontolog.evidence import load_evidence_graph

graph_app = typer.Typer(help="Inspect the evidence graph.")

@graph_app.callback(invoke_without_command=True)
def graph(
    show: Annotated[bool, typer.Option("--show", help="Print graph summary.")] = False,
    store_path: Annotated[Path, typer.Option("--store", help="SQLite database path.")] = Path("ontolog.db"),
) -> None:
    """Inspect the evidence graph (stub)."""
    if not show:
        typer.echo("Use --show to print graph summary.", err=True)
        raise typer.Exit(code=1)

    evidence_graph = load_evidence_graph(store_path)
    echo_status(f"nodes: {evidence_graph.node_count()}, edges: {evidence_graph.edge_count()}")
```

No `SqliteTemplateStore`, `EvidenceGraph()`, or store lifecycle in CLI — only arg parsing, one library call, and status output.

When extracting `ingest` / `templates`, preserve the same rule: call [`ingest_path`](file:///home/schult_v/projects/ontolog/src/ontolog/ingestion/reader.py) and [`extract_templates`](file:///home/schult_v/projects/ontolog/src/ontolog/templates/extractor.py) directly; do not duplicate pipeline logic in `commands.py`.

Shared option text (e.g. `--store`) can live in a small `cli/options.py` module if duplication becomes noisy — optional in Ch4.

### Red: `tests/unit/test_cli_graph.py`

| Test | Asserts |
|------|---------|
| `test_graph_show_exits_zero` | `CliRunner.invoke(app, ["graph", "--show"])` |
| `test_graph_show_prints_counts` | stderr contains `nodes:` and `edges:` |
| `test_graph_show_empty_counts` | stderr matches `nodes: 0` and `edges: 0` (stub — no inference yet) |
| `test_graph_show_opens_store` | With `--store` pointing at DB created by template extraction, still exits 0 (validates store path opens) |

**Expected failure:** typer exit / missing `graph` command

### Green

1. **Extract** existing `ingest` and `templates` handlers from `main.py` into `cli/ingest/commands.py` and `cli/templates/commands.py` — thin wrappers over existing library functions only.
2. **Add** `cli/graph/commands.py` — thin wrapper over `load_evidence_graph()` (see pattern above).
3. **Slim** `main.py` to registry + root callback only.

Optional: add `render_graph_summary(graph: EvidenceGraph)` to [`cli/output.py`](file:///home/schult_v/projects/ontolog/src/ontolog/cli/output.py) for Rich formatting — presentation only, no loading logic.

### Refactor

- Re-run existing [`test_cli.py`](file:///home/schult_v/projects/ontolog/tests/unit/test_cli.py) and [`test_cli_templates.py`](file:///home/schult_v/projects/ontolog/tests/unit/test_cli_templates.py) — must pass unchanged (import `app` from `ontolog.cli.main` still works)
- Share `--store` help text between `templates` and `graph` commands
- Add ruff per-file ignores for new `cli/*/commands.py` files (mirror `cli/main.py` ignores)

---

## Target file layout

```text
src/ontolog/
├── models/evidence.py              # NEW
├── models/__init__.py              # extend exports
├── evidence/
│   ├── __init__.py                 # NEW — export EvidenceGraph, load_evidence_graph
│   ├── graph.py                    # NEW — EvidenceGraph
│   └── loader.py                   # NEW — load_evidence_graph (library API)
└── cli/
    ├── main.py                     # REFACTOR — thin registry only
    ├── ingest/{__init__.py,commands.py}    # REFACTOR — extracted
    ├── templates/{__init__.py,commands.py} # REFACTOR — extracted
    └── graph/{__init__.py,commands.py}     # NEW — graph stub

tests/unit/
├── test_evidence_model.py          # NEW
├── test_evidence_graph.py          # NEW
├── test_evidence_loader.py         # NEW — library load API
└── test_cli_graph.py               # NEW — thin CLI wrapper only
```

---

## Documentation updates (post-implementation)

- [`docs/architecture.md`](file:///home/schult_v/projects/ontolog/docs/architecture.md) — brief evidence graph section
- [`docs/api.md`](file:///home/schult_v/projects/ontolog/docs/api.md) — document `EvidenceGraph`, models
- [`CHANGELOG.md`](file:///home/schult_v/projects/ontolog/CHANGELOG.md) — Ch4 entry
- [`.plans/README.md`](file:///home/schult_v/projects/ontolog/.plans/README.md) — add chapter_4 row

---

## Acceptance criteria

- [ ] Each TDD cycle: red failure confirmed before green implementation
- [ ] `Evidence`, `Node`, `Edge`, `NodeKind` frozen; score bounded 0–1
- [ ] `EvidenceGraph` add/query/attach_evidence works with NetworkX backing
- [ ] `to_json` / `from_json` round-trip is lossless for nodes, edges, and evidence
- [ ] `load_evidence_graph()` provides full graph-loading behavior in the library (CLI does not open stores)
- [ ] CLI uses one sub-package per command; `cli/main.py` is a thin `add_typer` registry; commands delegate to library
- [ ] `ontolog graph --show` prints `nodes: 0, edges: 0` (stub until Ch5 populates)
- [ ] Existing `test_cli.py` and `test_cli_templates.py` pass after ingest/templates extraction
- [ ] `ruff check`, `mypy src`, `pytest` green
- [ ] No providers, inference, aggregation, or graph SQLite persistence (scope guard)

---

## Explicit non-goals (Ch4)

- `EvidenceProvider` Protocol (Ch5)
- Populating graph from templates / running providers
- Graph persistence in SQLite (future chapter)
- `ontolog infer` / export commands
- Hypothesis property tests (Ch5)
- Public export of `EvidenceGraph` from top-level `ontolog` package (optional — export from `ontolog.evidence` only until Ch9)

---

## Suggested PR

**Title:** `feat: add evidence graph foundation`

**Branch:** `feat/ch4-evidence-graph`

```bash
pip install -e ".[dev]"
ruff check src tests && ruff format --check src tests
mypy src
pytest
ontolog graph --show
```

**Commit message (conventional):**

```
feat: add EvidenceGraph foundation with NetworkX backing

Introduces Evidence/Node/Edge models, JSON serialization, load_evidence_graph
library API, CLI sub-package layout, and thin graph --show wrapper.
```
