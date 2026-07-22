"""Relationship inference from graph evidence."""

from __future__ import annotations

from ontolog.config import ConfidenceThresholds
from ontolog.evidence.graph import EvidenceGraph
from ontolog.inference.event_nouns import event_noun_from_slug
from ontolog.inference.queries import collect_evidence, edges_with_label, nodes_by_kind
from ontolog.inference.scoring import combine_scores
from ontolog.models.candidate import InferenceResult, RelationshipCandidate
from ontolog.models.evidence import Edge, Evidence, Node, NodeKind
from ontolog.models.finding import ProviderInput
from ontolog.providers.ids import slugify

_ENTITY_FIELD_LABELS: frozenset[str] = frozenset({"interface"})
_MIN_EVENT_NOUN_EVENTS = 2


class RelationshipInferencePass:
    """Infer ownership and dependency relationships."""

    @property
    def name(self) -> str:
        """Return the inference pass identifier."""
        return "relationships"

    def infer(
        self,
        graph: EvidenceGraph,
        data: ProviderInput,
        *,
        thresholds: ConfidenceThresholds,
    ) -> InferenceResult:
        """Return relationship candidates."""
        return InferenceResult(
            relationships=_ownership_candidates(graph, data, thresholds.relationship),
        )


def _ownership_candidates(
    graph: EvidenceGraph,
    data: ProviderInput,
    min_confidence: float,
) -> tuple[RelationshipCandidate, ...]:
    """Infer ``owns`` relationships from graph structure and process context."""
    entity_names = _entity_display_names(graph)
    candidates: list[RelationshipCandidate] = []
    for edge in edges_with_label(graph, "has_field"):
        candidate = _owns_candidate_from_has_field(
            graph,
            edge,
            entity_names,
            min_confidence,
        )
        if candidate is not None:
            candidates.append(candidate)
    candidates.extend(_process_owns_event_noun_candidates(graph, data, min_confidence))
    return tuple(candidates)


def _process_owns_event_noun_candidates(
    graph: EvidenceGraph,
    data: ProviderInput,
    min_confidence: float,
) -> tuple[RelationshipCandidate, ...]:
    """Infer ``owns`` from a process entity to an event-derived noun entity."""
    process_slug = _single_process_slug(data)
    noun = _dominant_event_noun(graph)
    if process_slug is None or noun is None:
        return ()
    process_node = graph.get_node(f"entity:{process_slug}")
    if process_node is None:
        return ()
    confidence = _process_owns_noun_confidence(graph, noun)
    if confidence < min_confidence:
        return ()
    return (
        RelationshipCandidate(
            kind="owns",
            source_name=process_node.label,
            target_name=_title_case(noun),
            confidence=confidence,
            evidence=_process_owns_noun_evidence(graph, noun, process_node),
        ),
    )


def _single_process_slug(data: ProviderInput) -> str | None:
    """Return the sole process slug when all occurrences share one process."""
    slugs = {
        slugify(process)
        for occurrence in data.occurrences
        if (process := occurrence.process) is not None
    }
    if len(slugs) != 1:
        return None
    return next(iter(slugs))


def _dominant_event_noun(graph: EvidenceGraph) -> str | None:
    """Return the most common event noun prefix in the graph."""
    counts: dict[str, int] = {}
    for node in nodes_by_kind(graph, NodeKind.EVENT):
        noun = event_noun_from_slug(node.id.removeprefix("event:"))
        if noun is None:
            continue
        counts[noun] = counts.get(noun, 0) + 1
    if not counts:
        return None
    noun, count = max(counts.items(), key=lambda item: item[1])
    if count < _MIN_EVENT_NOUN_EVENTS:
        return None
    return noun


def _process_owns_noun_confidence(graph: EvidenceGraph, noun: str) -> float:
    """Combine evidence for a process-to-noun ownership link."""
    scores = [
        evidence.score
        for node in nodes_by_kind(graph, NodeKind.EVENT)
        if event_noun_from_slug(node.id.removeprefix("event:")) == noun
        for evidence in node.evidence
    ]
    return combine_scores(scores)


def _process_owns_noun_evidence(
    graph: EvidenceGraph,
    noun: str,
    process_node: Node,
) -> tuple[Evidence, ...]:
    """Return provenance for a process-to-noun ownership link."""
    event_evidence = tuple(
        evidence
        for node in nodes_by_kind(graph, NodeKind.EVENT)
        if event_noun_from_slug(node.id.removeprefix("event:")) == noun
        for evidence in collect_evidence(node)
    )
    return (*collect_evidence(process_node), *event_evidence)


def _entity_display_names(graph: EvidenceGraph) -> dict[str, str]:
    """Return display labels for entity nodes keyed by node id."""
    return {node.id: node.label for node in nodes_by_kind(graph, NodeKind.ENTITY)}


def _owns_candidate_from_has_field(
    graph: EvidenceGraph,
    edge: Edge,
    entity_names: dict[str, str],
    min_confidence: float,
) -> RelationshipCandidate | None:
    """Return an ``owns`` candidate when a structural field links to an entity."""
    source = graph.get_node(edge.source_id)
    target = graph.get_node(edge.target_id)
    if source is None or target is None:
        return None
    if not _is_structural_entity_field(target.label):
        return None
    confidence = _owns_confidence(edge, source)
    if confidence < min_confidence:
        return None
    return _build_owns_candidate(edge, source, target, entity_names, confidence)


def _is_structural_entity_field(label: str) -> bool:
    """Return whether ``label`` names a field promoted to an entity."""
    return label.lower() in _ENTITY_FIELD_LABELS


def _owns_confidence(edge: Edge, source: Node) -> float:
    """Combine relationship evidence from the edge and owning entity."""
    scores = [item.score for item in edge.evidence] + [item.score for item in source.evidence]
    return combine_scores(scores)


def _build_owns_candidate(
    edge: Edge,
    source: Node,
    target: Node,
    entity_names: dict[str, str],
    confidence: float,
) -> RelationshipCandidate:
    """Build an ``owns`` relationship between an entity and a structural field."""
    return RelationshipCandidate(
        kind="owns",
        source_name=entity_names.get(source.id, source.label),
        target_name=_title_case(target.label.lower()),
        confidence=confidence,
        evidence=(*collect_evidence(edge), *collect_evidence(source)),
    )


def _title_case(value: str) -> str:
    """Return a title-cased display name."""
    return value.replace("_", " ").title()
