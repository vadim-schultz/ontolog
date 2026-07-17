---
name: Ontolog Chapter 7
overview: Chapter 7 merges InferenceResult candidates into ProbabilisticDomainModel via tier-weighted aggregation with alternatives, export eligibility, and full provenance.
status: complete
---

# Chapter 7 — Probabilistic aggregation and domain model

**Status:** Complete on branch `feat/ch7-aggregation`

## Delivered

| Deliverable | Location |
|-------------|----------|
| Domain model types | `src/ontolog/models/domain.py` |
| Tier-weighted scoring | `src/ontolog/inference/aggregate/scoring.py` |
| Per-concept aggregators | `src/ontolog/inference/aggregate/{entities,events,fields,relationships,states}.py` |
| Orchestrator | `src/ontolog/inference/aggregate/__init__.py` → `aggregate_inference_result()` |
| Pipeline entry point | `build_domain_model()` in `src/ontolog/inference/builder.py` |
| Source weights config | `EvidenceSourceTier`, `EvidenceSourceWeights` in `config.py` |

## Tests

- `tests/unit/test_domain_model.py`
- `tests/unit/test_aggregate_scoring.py`
- `tests/unit/test_aggregate_entities.py`
- `tests/unit/test_aggregate_fields.py`
- `tests/unit/test_aggregate_conflicts.py`
- `tests/unit/test_aggregate_integration.py`
- `aggregate_fixture()` helper in `tests/helpers.py`

## Acceptance criteria

- [x] Tier priority: human > deterministic > LLM
- [x] Conflicting field types → primary + alternatives
- [x] `export_eligible` from `ConfidenceThresholds.export`
- [x] JSON round-trip with confidence + provenance per claim
- [x] Reproducible aggregation output
- [x] `build_domain_model()` on controlboard + order_lifecycle fixtures
