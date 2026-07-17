---
name: Ontolog Chapter 6
overview: Chapter 6 adds the inference engine — four graph-driven inference passes (entities, events, fields, relationships, states) behind an InferencePass Protocol, frozen candidate models, scoring helpers that combine provider evidence, a run_inference orchestrator invoked after providers, and fixture-only integration tests for controlboard and order_lifecycle — implemented via eight red-green-refactor TDD cycles following chapter_5.plan.md conventions.
todos:
  - id: prereq-scoring-config
    content: "Prerequisite: combine_scores helper, InferenceKind + InferenceConfig in config.py, graph query helpers"
    status: pending
  - id: tdd-cycle-1
    content: "RED→GREEN→REFACTOR: Candidate models, InferenceResult, InferencePass Protocol, registry, run_inference skeleton (test_inference_registry.py)"
    status: pending
  - id: tdd-cycle-2
    content: "RED→GREEN→REFACTOR: Entity inference — ControlBoard + Interface from graph (test_inference_entities.py)"
    status: pending
  - id: tdd-cycle-3
    content: "RED→GREEN→REFACTOR: Event inference — verb lexicon + PacketSent/Received/ConnectionEstablished (test_inference_events.py)"
    status: pending
  - id: tdd-cycle-4
    content: "RED→GREEN→REFACTOR: Field inference — payload/destination types with documented confidence (test_inference_fields.py)"
    status: pending
  - id: tdd-cycle-5
    content: "RED→GREEN→REFACTOR: Relationship inference — ControlBoard owns Interface (test_inference_relationships.py)"
    status: pending
  - id: tdd-cycle-6
    content: "RED→GREEN→REFACTOR: State machine inference — order_lifecycle created→validated→running→completed (test_inference_states.py)"
    status: pending
  - id: tdd-cycle-7
    content: "RED→GREEN→REFACTOR: build_inference_result library API + integration tests"
    status: pending
  - id: tdd-cycle-8
    content: "RED→GREEN→REFACTOR: Optional graph CLI summary hook (candidate counts) + Hypothesis combine_scores property"
    status: pending
  - id: docs-changelog
    content: Update docs/api.md, architecture.md, CHANGELOG.md, .plans/README.md
    status: pending
isProject: false
---

# Chapter 6 — Inference engine (events, entities, relationships, states)

**Artifact path:** [`.plans/chapter_6.plan.md`](file:///home/schult_v/projects/ontolog/.plans/chapter_6.plan.md) (update [`.plans/README.md`](file:///home/schult_v/projects/ontolog/.plans/README.md) on completion)

## TDD methodology

Every capability follows **red → green → refactor** (same as [chapter_5.plan.md](file:///home/schult_v/projects/ontolog/.plans/chapter_5.plan.md)):

1. **Red** — write tests asserting behavior; run `pytest <test_file> -x` and confirm meaningful failure
2. **Green** — smallest production change to pass
3. **Refactor** — extract helpers; re-run narrow test file, then full gate

```bash
pytest tests/unit/test_inference_registry.py -x   # per cycle
ruff check src tests && ruff format --check src tests && mypy src && pytest
```

---

## Starting point (Chapter 5 complete)

| Area | Status |
|------|--------|
| [`EvidenceGraph`](file:///home/schult_v/projects/ontolog/src/ontolog/evidence/graph.py) | Mutable graph; nodes/edges with attached `Evidence` |
| [`load_evidence_graph()`](file:///home/schult_v/projects/ontolog/src/ontolog/evidence/loader.py) | Runs six providers; populates graph from SQLite store |
| [`run_providers()`](file:///home/schult_v/projects/ontolog/src/ontolog/evidence/runner.py) | Applies `EvidenceFinding` mutations in provider order |
| Six providers | Namespace, Regex, Statistics, CoOccurrence, Temporal, Process |
| Node ID scheme | `entity:`, `field:`, `type:`, `event:`, `template:` via [`providers/ids.py`](file:///home/schult_v/projects/ontolog/src/ontolog/providers/ids.py) |
| [`ConfidenceThresholds`](file:///home/schult_v/projects/ontolog/src/ontolog/config.py) | `field`, `entity`, `event`, `relationship` — **not wired to inference yet** |
| `inference/` | **Does not exist** |
| Candidate models | **Do not exist** — Ch7 `ProbabilisticDomainModel` is separate |
| Fixtures | [`controlboard.log`](file:///home/schult_v/projects/ontolog/tests/fixtures/controlboard.log) (60 lines, 3 event families); [`order_lifecycle.log`](file:///home/schult_v/projects/ontolog/tests/fixtures/order_lifecycle.log) (15 lines, 4-state cycle × 3) |

**What Ch5 already puts in the graph (controlboard):**

| Node / edge | Source provider |
|-------------|-----------------|
| `entity:controlboard` | NamespaceProvider (process name) |
| `event:packet_sent`, `event:packet_received`, `event:connection_established` | NamespaceProvider (template prefix) |
| `field:{template_id}:destination`, `payload`, `interface`, … | NamespaceProvider |
| `entity:controlboard --has_field--> field:…` | NamespaceProvider |
| `field:… --has_type--> type:ipv4` / `type:hex` | RegexProvider |
| reinforced scores on fields | StatisticsProvider |
| `field:* --co_occurs--> field:*` | CoOccurrenceProvider |
| `template:* --follows--> template:*` | TemporalProvider |
| `template:* --repeats_in_process--> template:*` | ProcessProvider |

Ch6 **reads** this graph and **promotes** nodes/edges into structured **candidates** with combined confidence and provenance — it does not re-run Drain3 or duplicate provider heuristics.

---

## Goal

Turn provider evidence into structured domain concepts ready for Ch7 aggregation.

```mermaid
flowchart TD
    store[SqliteTemplateStore] --> loader[load_evidence_graph]
    loader --> graph[EvidenceGraph_populated]
    graph --> orchestrator[run_inference]
    templates[list_templates] --> input[ProviderInput]
    occurrences[list_occurrences] --> input
    input --> orchestrator
    config[InferenceConfig] --> registry[inference_registry]
    registry --> orchestrator
    orchestrator --> result[InferenceResult]
    result -.-> ch7[Ch7_Aggregation]
```

**Library-first rule:** All inference logic lives under `src/ontolog/inference/` and `src/ontolog/models/candidate.py`. CLI remains a thin adapter — Ch6 may add candidate **counts** to `ontolog graph --show`; full `ontolog infer` is Ch9.

```python
from pathlib import Path
from ontolog.config import default_config
from ontolog.inference import build_inference_result

result = build_inference_result(Path("ontolog.db"), config=default_config())
# Ch6: result.entities, result.events, result.fields, result.relationships, result.state_machines
```

**MVP target (controlboard + order_lifecycle):**

```
Entities: ControlBoard, Interface
Events: PacketSent, PacketReceived, ConnectionEstablished
Fields: payload (hex, ~0.98), destination (ipv4, ~1.0)
Relationship: ControlBoard owns Interface
State machine: created → validated → running → completed (order_lifecycle)
```

Each candidate carries `confidence` plus `evidence: tuple[Evidence, ...]` tracing back to provider sources.

---

## OOP / design conventions

| Layer | Pattern | Ch6 application |
|-------|---------|-----------------|
| Extension point | `Protocol` in [`types.py`](file:///home/schult_v/projects/ontolog/src/ontolog/types.py) | `InferencePass` with `name` + `infer` |
| Pass variants | One module per concept family (Rule of 3+) | `entities.py`, `events.py`, `fields.py`, `relationships.py`, `states.py` |
| Selection | Factory | `inference_registry(config) -> tuple[InferencePass, ...]` |
| Orchestration | Module-level function | `run_inference()` in `inference/runner.py` |
| Graph reads | Pure query helpers | `inference/queries.py` — nodes by kind, edges by label, type of field |
| Scoring | Pure functions | `inference/scoring.py` — `combine_scores()`, reuse `reinforce_score` from evidence |
| Domain values | Frozen Pydantic | `EntityCandidate`, `EventCandidate`, … in `models/candidate.py` |
| Pipeline output | Frozen Pydantic | `InferenceResult` bundles all candidate tuples |

**Ch6 vs Ch7 boundary:**

| Ch6 (`InferenceResult`) | Ch7 (`ProbabilisticDomainModel`) |
|-------------------------|----------------------------------|
| Candidates with alternatives possible per pass | Single merged model per concept |
| Confidence = combine provider scores on graph | Weighted aggregation + human/LLM weights |
| No export eligibility filtering | `ConfidenceThresholds.export` applied |
| JSON-serializable for debugging | Canonical domain model export |

Ch6 does **not** implement `inference/aggregate.py` (reserved for Ch7).

---

## Prerequisite — scoring, config, graph queries

Before TDD Cycle 1:

### 1. `combine_scores()` in `inference/scoring.py`

Independent-evidence combination (documented in docstring):

```python
def combine_scores(scores: Sequence[float]) -> float:
    """Combine independent evidence scores into one confidence in [0, 1]."""
    product = 1.0
    for score in scores:
        product *= 1.0 - score
    return 1.0 - product
```

Red tests in `tests/unit/test_inference_scoring.py` including Hypothesis:

- `combine_scores([s]) == s`
- `combine_scores([]) == 0.0` (no evidence → zero confidence)
- Monotonic: adding a score ≥ existing max never decreases result

### 2. `InferenceConfig` in [`config.py`](file:///home/schult_v/projects/ontolog/src/ontolog/config.py)

```python
class InferenceKind(StrEnum):
    ENTITIES = "entities"
    EVENTS = "events"
    FIELDS = "fields"
    RELATIONSHIPS = "relationships"
    STATES = "states"

class InferenceConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    enabled: frozenset[InferenceKind] = Field(default_factory=lambda: frozenset(InferenceKind))

# Extend OntologConfig:
inference: InferenceConfig = Field(default_factory=InferenceConfig)
```

### 3. Graph query helpers — `inference/queries.py`

Pure functions over `EvidenceGraph` (no mutation):

| Function | Returns |
|----------|---------|
| `nodes_by_kind(graph, kind)` | `tuple[Node, ...]` |
| `edges_with_label(graph, label)` | `tuple[Edge, ...]` |
| `field_type_name(graph, field_node_id)` | `str | None` via `has_type` edge target label |
| `entity_fields(graph, entity_node_id)` | field node ids from `has_field` edges |
| `max_evidence_score(node_or_edge, *, source=None)` | highest matching `Evidence.score` |

Red tests in `tests/unit/test_inference_queries.py` using small inline graphs built in tests.

---

## TDD Cycle 1 — Protocol, candidates, registry, orchestrator skeleton

### Red: `tests/unit/test_inference_registry.py`

| Test | Asserts |
|------|---------|
| `test_entity_candidate_construct` | Frozen `EntityCandidate` with name, slug, confidence, evidence |
| `test_inference_result_empty` | `InferenceResult()` has empty tuples for all candidate kinds |
| `test_registry_default_all_enabled` | `len(inference_registry(default_config().inference)) == 5` |
| `test_registry_respects_disabled` | Disable `STATES` → registry excludes state pass |
| `test_run_inference_empty_graph` | Empty graph → empty `InferenceResult`, no error |
| `test_run_inference_merges_pass_outputs` | Stub passes append to result buckets |

**Expected failure:** `ModuleNotFoundError: ontolog.inference`

### Green

| File | Contents |
|------|----------|
| [`models/candidate.py`](file:///home/schult_v/projects/ontolog/src/ontolog/models/candidate.py) | All candidate models + `InferenceResult` |
| [`types.py`](file:///home/schult_v/projects/ontolog/src/ontolog/types.py) | `InferencePass` Protocol |
| [`inference/base.py`](file:///home/schult_v/projects/ontolog/src/ontolog/inference/base.py) | `inference_registry()`, `DEFAULT_INFERENCE_ORDER` |
| [`inference/runner.py`](file:///home/schult_v/projects/ontolog/src/ontolog/inference/runner.py) | `run_inference()` merges pass partial results |
| [`inference/__init__.py`](file:///home/schult_v/projects/ontolog/src/ontolog/inference/__init__.py) | export `run_inference`, `build_inference_result` (stub) |
| Stub pass modules | Return empty tuples until their cycles land |

```python
class InferencePass(Protocol):
    @property
    def name(self) -> str: ...
    def infer(
        self,
        graph: EvidenceGraph,
        data: ProviderInput,
        *,
        thresholds: ConfidenceThresholds,
    ) -> InferenceResult: ...
```

Each pass returns an `InferenceResult` with only its bucket filled; orchestrator concatenates tuples.

### Refactor

- Export candidate models from [`models/__init__.py`](file:///home/schult_v/projects/ontolog/src/ontolog/models/__init__.py)
- Export `run_inference` from `inference/__init__.py`

---

## TDD Cycle 2 — Entity inference (`entities.py`)

### Red: `tests/unit/test_inference_entities.py`

Build graph via `run_providers` on inline controlboard-like `ProviderInput` (reuse pattern from [`test_provider_namespace.py`](file:///home/schult_v/projects/ontolog/tests/unit/test_provider_namespace.py)).

| Test | Asserts |
|------|---------|
| `test_process_entity_promoted` | `entity:controlboard` → `EntityCandidate(name="ControlBoard", slug="controlboard")` |
| `test_interface_field_yields_interface_entity` | Field label `interface` across templates → `EntityCandidate(name="Interface")` |
| `test_entity_confidence_from_namespace_evidence` | Base namespace score 0.8 present in `evidence` tuple |
| `test_unknown_entity_not_invented` | Graph without entity nodes → empty `entities` |

**Interface heuristic (document in module docstring):**

- Collect FIELD nodes whose `label == "interface"` (case-insensitive)
- Require field linked to an entity via `has_field` OR seen in ≥ 2 distinct templates
- Emit `EntityCandidate(name="Interface", slug="interface", confidence=combine_scores(...))`

### Green: [`inference/entities.py`](file:///home/schult_v/projects/ontolog/src/ontolog/inference/entities.py)

1. Promote all `NodeKind.ENTITY` nodes → `EntityCandidate` (title-case label, slug from id)
2. Run interface noun-phrase heuristic on FIELD nodes
3. Deduplicate by slug; keep higher confidence

### Refactor

- `_title_case(slug: str) -> str` helper (~3 LOC)
- `_promote_entity_node(node: Node) -> EntityCandidate`

---

## TDD Cycle 3 — Event inference (`events.py`)

### Red: `tests/unit/test_inference_events.py`

| Test | Asserts |
|------|---------|
| `test_packet_sent_verbs` | `PacketSent` → verbs contains `"send"` |
| `test_packet_received_verbs` | `PacketReceived` → verbs contains `"receive"` |
| `test_connection_established_verbs` | `ConnectionEstablished` → verbs contains `"connect"` |
| `test_lifecycle_create_verb` | `OrderCreated` → verbs contains `"create"` |
| `test_frequency_boosts_confidence` | Event node with statistics evidence scores higher than namespace-only |
| `test_non_event_nodes_ignored` | ENTITY nodes not promoted as events |

### Green: [`inference/events.py`](file:///home/schult_v/projects/ontolog/src/ontolog/inference/events.py)

**Verb lexicon** (`_VERB_PATTERNS: dict[str, tuple[str, ...]]`):

| Verb | Substring patterns (case-insensitive on event slug/label) |
|------|-----------------------------------------------------------|
| `send` | `sent`, `send` |
| `receive` | `received`, `receive` |
| `connect` | `connect`, `established` |
| `create` | `create`, `created` |
| `delete` | `delete`, `deleted`, `removed` |
| `update` | `update`, `updated`, `validated` |

Algorithm:

1. Promote `NodeKind.EVENT` nodes
2. Match slug against lexicon → `frozenset` of verbs (may be empty)
3. `confidence = combine_scores(all evidence scores on event node)`

### Refactor

- `_verbs_for_slug(slug: str) -> frozenset[str]` pure helper
- Lexicon as module-level constant for testability

---

## TDD Cycle 4 — Field inference (`fields.py`)

### Red: `tests/unit/test_inference_fields.py`

Use controlboard provider pipeline graph (regex + statistics on destination/payload).

| Test | Asserts |
|------|---------|
| `test_destination_ipv4_field` | Field `destination` → `type_name="ipv4"` |
| `test_payload_hex_field` | Field `payload` → `type_name="hex"` |
| `test_destination_confidence_documented` | `confidence >= 0.95` (regex 0.95 + statistics reinforcement → ~1.0) |
| `test_payload_confidence_documented` | `confidence >= 0.95` and typically `>= 0.98` with 60 controlboard repetitions |
| `test_untyped_field_excluded` | Field without `has_type` edge → not in result (or confidence below `thresholds.field`) |
| `test_provenance_includes_regex_and_statistics` | `evidence` sources include `"regex"` and optionally `"statistics"` |

**Documented confidence table** (assert in integration test, explain in `fields.py` docstring):

| Field | Type | Expected confidence | Evidence sources |
|-------|------|---------------------|------------------|
| `destination` | `ipv4` | ≥ 0.95 (typically ~1.0) | regex (0.95) + statistics reinforcement |
| `payload` | `hex` | ≥ 0.95 (typically ~0.98) | regex (0.95) + statistics reinforcement |

### Green: [`inference/fields.py`](file:///home/schult_v/projects/ontolog/src/ontolog/inference/fields.py)

1. Iterate `NodeKind.FIELD` nodes
2. Resolve type via `field_type_name(graph, field_id)` (follow `has_type` edge)
3. Gather all `Evidence` from field node + type edge + statistics attachments
4. `confidence = combine_scores(scores)`; filter by `thresholds.field`

### Refactor

- Reuse `inference/queries.py` for type resolution
- Single `_field_candidate(graph, node, thresholds)` helper

---

## TDD Cycle 5 — Relationship inference (`relationships.py`)

### Red: `tests/unit/test_inference_relationships.py`

| Test | Asserts |
|------|---------|
| `test_owns_from_has_field` | `entity:controlboard --has_field--> field:…:interface` → `RelationshipCandidate(kind="owns", source="ControlBoard", target="Interface")` |
| `test_owns_confidence` | `confidence >= 0.6` (namespace has_field 0.7) |
| `test_co_occurrence_not_duplicated_as_owns` | `co_occurs` between payload/destination does not emit `owns` |
| `test_dependency_from_follows` | Optional: `kind="precedes"` from temporal `follows` between event nodes (lower priority — implement if straightforward) |

**Primary MVP relationship:** `owns` from `has_field` where field label maps to a promoted entity (`interface` → `Interface`).

### Green: [`inference/relationships.py`](file:///home/schult_v/projects/ontolog/src/ontolog/inference/relationships.py)

1. Walk `has_field` edges from entity → field
2. If field label matches a promoted entity slug/name (from entities pass output passed via graph re-query), emit `owns`
3. `confidence = combine_scores(evidence on has_field edge + entity evidence)`
4. Filter by `thresholds.relationship`

**Cross-pass dependency:** Relationship pass runs **after** entity pass in orchestrator; it re-reads entity nodes from graph rather than requiring `InferenceResult` injection (keeps passes independent). Interface entity must exist in graph as FIELD + inferred EntityCandidate slug `interface`.

### Refactor

- `_owns_relationship(graph, entity_node, field_node) -> RelationshipCandidate | None`

---

## TDD Cycle 6 — State machine inference (`states.py`)

### Red: `tests/unit/test_inference_states.py`

Use `order_lifecycle.log` extracted templates + full provider pipeline.

| Test | Asserts |
|------|---------|
| `test_lifecycle_states_detected` | States include `created`, `validated`, `running`, `completed` |
| `test_transition_sequence` | Transitions include `created→validated`, `validated→running`, `running→completed` |
| `test_transition_counts` | Each transition count ≥ 3 (fixture repeats cycle 3×; line 15 truncates last `completed`) |
| `test_state_machine_confidence` | `confidence >= 0.6` |
| `test_no_states_from_controlboard` | Controlboard graph → empty `state_machines` (no status lifecycle) |

**Signals (combine, documented):**

1. **Status parameter mining** — occurrences with `status=` param; ordered by timestamp; count adjacent value pairs
2. **Temporal `follows` edges** — map template ids to status/event labels via templates tuple in `ProviderInput`
3. **Markov heuristic** — keep transitions with count ≥ `min_support` (default 2); states = sorted unique endpoints

Emit one `StateMachineCandidate(name="OrderLifecycle", states=..., transitions=...)`.

### Green: [`inference/states.py`](file:///home/schult_v/projects/ontolog/src/ontolog/inference/states.py)

### Refactor

- `_transition_counts_from_status_param(occurrences) -> Counter[tuple[str, str]]`
- `_merge_transition_counts(a, b) -> Counter` if using both signals

---

## TDD Cycle 7 — `build_inference_result` + integration tests

### Red

| File | Tests |
|------|-------|
| `tests/unit/test_inference_builder.py` | `build_inference_result` calls providers then inference; respects `InferenceConfig` |
| `tests/integration/test_inference_controlboard.py` | Full MVP assertions on controlboard fixture |
| `tests/integration/test_inference_order_lifecycle.py` | State machine assertions |

**`test_inference_controlboard.py` acceptance:**

```python
result = build_inference_result(store_path, config=default_config())
entity_names = {e.name for e in result.entities}
event_names = {e.name for e in result.events}
assert entity_names >= {"ControlBoard", "Interface"}
assert event_names >= {"PacketSent", "PacketReceived", "ConnectionEstablished"}
dest = next(f for f in result.fields if f.name == "destination")
payload = next(f for f in result.fields if f.name == "payload")
assert dest.type_name == "ipv4" and dest.confidence >= 0.95
assert payload.type_name == "hex" and payload.confidence >= 0.95
owns = next(r for r in result.relationships if r.kind == "owns")
assert owns.source_name == "ControlBoard" and owns.target_name == "Interface"
```

### Green: [`inference/builder.py`](file:///home/schult_v/projects/ontolog/src/ontolog/inference/builder.py)

```python
def build_inference_result(
    store_path: Path,
    *,
    config: OntologConfig,
) -> InferenceResult:
    store = SqliteTemplateStore(store_path)
    try:
        templates = store.list_templates()
        occurrences = store.list_occurrences()
        data = ProviderInput(templates=tuple(templates), occurrences=tuple(occurrences))
        graph = EvidenceGraph()
        run_providers(graph, data, provider_registry(config.providers))
        return run_inference(
            graph,
            data,
            inference_registry(config.inference),
            thresholds=config.confidence,
        )
    finally:
        store.close()
```

**Pre-alpha API rule:** `build_inference_result` requires explicit `config` — no silent `default_config()` inside (callers pass `default_config()`).

### Refactor

- Consider thin wrapper `load_inference_result = build_inference_result` alias if naming clarity helps
- `InferenceResult.model_dump_json()` for debugging (add round-trip test optional)

---

## TDD Cycle 8 — CLI summary + scoring property test

### Red: extend [`test_cli_graph.py`](file:///home/schult_v/projects/ontolog/tests/unit/test_cli_graph.py)

| Test | Asserts |
|------|---------|
| `test_graph_show_includes_candidate_counts` | After templates + inference, output includes `entities: N` with `N > 0` |

Optional — only if minimal diff:

- [`cli/graph/commands.py`](file:///home/schult_v/projects/ontolog/src/ontolog/cli/graph/commands.py) calls `build_inference_result` after `load_evidence_graph` and prints candidate counts (not full dump)

### Red: `tests/unit/test_inference_scoring.py` (Hypothesis)

| Test | Asserts |
|------|---------|
| `test_combine_scores_bounded` | Result in `[0, 1]` |
| `test_combine_scores_monotonic_with_extra_evidence` | Adding higher score does not decrease |

### Green

Wire CLI summary; ensure `combine_scores` Hypothesis test passes.

---

## Inference pass execution order

```python
DEFAULT_INFERENCE_ORDER: tuple[InferenceKind, ...] = (
    InferenceKind.ENTITIES,       # promote entities + Interface heuristic
    InferenceKind.EVENTS,         # promote events + verbs
    InferenceKind.FIELDS,         # field types (uses graph types)
    InferenceKind.RELATIONSHIPS,  # owns (uses entity + field labels)
    InferenceKind.STATES,         # lifecycle state machines
)
```

```mermaid
flowchart LR
    providers[run_providers] --> graph[EvidenceGraph]
    graph --> entities[EntityPass]
    entities --> events[EventPass]
    events --> fields[FieldPass]
    fields --> relationships[RelationshipPass]
    relationships --> states[StatePass]
    states --> result[InferenceResult]
```

Providers always run **before** inference (in `build_inference_result` or when caller invokes `run_providers` then `run_inference` separately).

---

## Target file layout

```text
src/ontolog/
├── config.py                       # + InferenceKind, InferenceConfig
├── types.py                        # + InferencePass Protocol
├── models/
│   ├── candidate.py                # NEW — all candidate models + InferenceResult
│   └── __init__.py                 # extend exports
├── inference/
│   ├── __init__.py                 # NEW — run_inference, build_inference_result
│   ├── base.py                     # NEW — registry + order
│   ├── runner.py                   # NEW — run_inference orchestrator
│   ├── builder.py                  # NEW — build_inference_result
│   ├── scoring.py                  # NEW — combine_scores
│   ├── queries.py                  # NEW — graph read helpers
│   ├── entities.py                 # NEW
│   ├── events.py                   # NEW
│   ├── fields.py                   # NEW
│   ├── relationships.py            # NEW
│   └── states.py                   # NEW
└── cli/graph/commands.py           # EXTEND — optional candidate counts

tests/
├── unit/
│   ├── test_inference_registry.py  # NEW
│   ├── test_inference_queries.py   # NEW
│   ├── test_inference_scoring.py   # NEW — Hypothesis
│   ├── test_inference_entities.py  # NEW
│   ├── test_inference_events.py    # NEW
│   ├── test_inference_fields.py    # NEW
│   ├── test_inference_relationships.py  # NEW
│   ├── test_inference_states.py    # NEW
│   ├── test_inference_builder.py   # NEW
│   └── test_cli_graph.py           # EXTEND
└── integration/
    ├── test_inference_controlboard.py    # NEW
    └── test_inference_order_lifecycle.py # NEW
```

---

## Candidate model sketches

```python
class EntityCandidate(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    slug: str
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    graph_node_id: str
    evidence: tuple[Evidence, ...] = ()

class EventCandidate(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    slug: str
    verbs: frozenset[str] = Field(default_factory=frozenset)
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    graph_node_id: str
    evidence: tuple[Evidence, ...] = ()

class FieldCandidate(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    type_name: str
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    graph_node_id: str
    evidence: tuple[Evidence, ...] = ()

class RelationshipCandidate(BaseModel):
    model_config = ConfigDict(frozen=True)
    kind: str  # "owns", "precedes", …
    source_name: str
    target_name: str
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    evidence: tuple[Evidence, ...] = ()

class StateTransition(BaseModel):
    model_config = ConfigDict(frozen=True)
    from_state: str
    to_state: str
    count: int = Field(ge=1)
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]

class StateMachineCandidate(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    states: tuple[str, ...]
    transitions: tuple[StateTransition, ...]
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    evidence: tuple[Evidence, ...] = ()

class InferenceResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    entities: tuple[EntityCandidate, ...] = ()
    events: tuple[EventCandidate, ...] = ()
    fields: tuple[FieldCandidate, ...] = ()
    relationships: tuple[RelationshipCandidate, ...] = ()
    state_machines: tuple[StateMachineCandidate, ...] = ()
```

---

## Documentation updates (post-implementation)

- [`docs/architecture.md`](file:///home/schult_v/projects/ontolog/docs/architecture.md) — inference pipeline section after providers
- [`docs/api.md`](file:///home/schult_v/projects/ontolog/docs/api.md) — `build_inference_result`, `run_inference`, candidate models, `InferenceConfig`
- [`CHANGELOG.md`](file:///home/schult_v/projects/ontolog/CHANGELOG.md) — Ch6 entry
- [`.plans/README.md`](file:///home/schult_v/projects/ontolog/.plans/README.md) — add chapter_6 row; mark Ch6 complete

---

## Acceptance criteria

- [ ] Each TDD cycle: red failure confirmed before green implementation
- [ ] Five inference passes behind `InferencePass` Protocol; registry honors enable/disable
- [ ] Controlboard → `ControlBoard`, `Interface`, `PacketSent`, `PacketReceived`, `ConnectionEstablished`
- [ ] `destination` → ipv4 with `confidence >= 0.95`; `payload` → hex with `confidence >= 0.95`
- [ ] `ControlBoard owns Interface` relationship suggested with `confidence >= thresholds.relationship`
- [ ] `order_lifecycle.log` → state sequence `created → validated → running → completed`
- [ ] `combine_scores` monotonic property under Hypothesis
- [ ] All tests use fixtures only — no network, no LLM
- [ ] `build_inference_result()` runs providers then inference from SQLite store
- [ ] `ruff check`, `mypy src`, `pytest` green

---

## Explicit non-goals (Ch6)

- `ProbabilisticDomainModel`, `inference/aggregate.py`, Bayesian merging (Ch7)
- Export layer, `ontolog infer` / `ontolog export` (Ch8–9)
- LLM / semantic providers (Ch10)
- Human feedback integration (Ch11)
- Graph SQLite persistence for candidates
- NLP / embeddings for noun phrases beyond simple field-label heuristics
- Multiple competing candidates per slug in `InferenceResult` (Ch7 keeps alternatives)

---

## Suggested PR

**Title:** `feat: add inference engine for domain candidates`

**Branch:** `feat/ch6-inference-engine`

```bash
pip install -e ".[dev]"
ruff check src tests && ruff format --check src tests
mypy src
pytest
pytest tests/integration/test_inference_controlboard.py -v
pytest tests/integration/test_inference_order_lifecycle.py -v
```

**Commit message:**

```
feat(inference): add entity, event, field, relationship, and state inference

Introduces candidate models, five inference passes, combine_scores helper,
build_inference_result pipeline (providers then inference), and controlboard
plus order_lifecycle integration tests.
```
