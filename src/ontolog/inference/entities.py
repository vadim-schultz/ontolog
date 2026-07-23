"""Entity inference from graph evidence."""

from __future__ import annotations

from collections import Counter

from ontolog.config import ConfidenceThresholds
from ontolog.evidence.graph import EvidenceGraph
from ontolog.inference.event_nouns import event_noun_from_slug
from ontolog.inference.hierarchy import (
    STRUCTURAL_FIELD_LABELS,
    build_hierarchy_index,
    ordered_entity_chain,
)
from ontolog.inference.queries import collect_evidence, edges_with_label, nodes_by_kind
from ontolog.inference.scoring import combine_scores
from ontolog.models.candidate import EntityCandidate, InferenceResult
from ontolog.models.evidence import Evidence, Node, NodeKind
from ontolog.models.finding import ProviderInput
from ontolog.providers.ids import slugify

_INTERFACE_LABEL = "interface"
_MIN_STRUCTURAL_TEMPLATES = 2
_MIN_EVENT_NOUN_EVENTS = 2


class EntityInferencePass:
    """Promote entity nodes and infer noun-phrase entities from fields."""

    @property
    def name(self) -> str:
        """Return the inference pass identifier."""
        return "entities"

    def infer(
        self,
        graph: EvidenceGraph,
        data: ProviderInput,
        *,
        thresholds: ConfidenceThresholds,
    ) -> InferenceResult:
        """Return entity candidates."""
        candidates = _graph_entity_candidates(graph, thresholds.entity)
        for label in STRUCTURAL_FIELD_LABELS:
            _merge_entity_candidate(candidates, _structural_entity(graph, label), thresholds.entity)
        for candidate in _event_noun_entities(graph, thresholds.entity):
            _merge_entity_candidate(candidates, candidate, thresholds.entity)
        for candidate in _hierarchy_entities(graph, data, thresholds.entity):
            _merge_entity_candidate(candidates, candidate, thresholds.entity)
        return InferenceResult(entities=tuple(candidates.values()))


def _graph_entity_candidates(
    graph: EvidenceGraph,
    min_confidence: float,
) -> dict[str, EntityCandidate]:
    """Promote entity nodes from the graph."""
    candidates: dict[str, EntityCandidate] = {}
    for node in nodes_by_kind(graph, NodeKind.ENTITY):
        _merge_entity_candidate(candidates, _promote_entity_node(node), min_confidence)
    return candidates


def _merge_entity_candidate(
    candidates: dict[str, EntityCandidate],
    candidate: EntityCandidate | None,
    min_confidence: float,
) -> None:
    """Insert ``candidate`` when it meets the threshold and beats any existing slug."""
    if candidate is None or candidate.confidence < min_confidence:
        return
    existing = candidates.get(candidate.slug)
    if existing is None or candidate.confidence > existing.confidence:
        candidates[candidate.slug] = candidate


def _promote_entity_node(node: Node) -> EntityCandidate:
    slug = node.id.removeprefix("entity:")
    return EntityCandidate(
        name=_title_case(slug),
        slug=slug,
        confidence=combine_scores([evidence.score for evidence in node.evidence]),
        graph_node_id=node.id,
        evidence=collect_evidence(node),
    )


def _structural_entity(graph: EvidenceGraph, label: str) -> EntityCandidate | None:
    """Infer an entity promoted from a structural field label."""
    field_nodes = _structural_field_nodes(graph, label)
    if not field_nodes or not _structural_signal_sufficient(graph, field_nodes):
        return None
    return _build_structural_candidate(graph, label, field_nodes)


def _structural_field_nodes(graph: EvidenceGraph, label: str) -> tuple[Node, ...]:
    """Return field nodes whose label matches ``label``."""
    lowered = label.lower()
    return tuple(
        node for node in nodes_by_kind(graph, NodeKind.FIELD) if node.label.lower() == lowered
    )


def _structural_signal_sufficient(
    graph: EvidenceGraph,
    field_nodes: tuple[Node, ...],
) -> bool:
    """Return whether structural fields are linked or span enough templates."""
    if _structural_has_field_link(graph, field_nodes):
        return True
    template_ids = {_template_id_from_field(node.id) for node in field_nodes}
    return len(template_ids) >= _MIN_STRUCTURAL_TEMPLATES


def _structural_has_field_link(
    graph: EvidenceGraph,
    field_nodes: tuple[Node, ...],
) -> bool:
    """Return whether any structural field has a ``has_field`` edge."""
    field_ids = {node.id for node in field_nodes}
    return any(edge.target_id in field_ids for edge in edges_with_label(graph, "has_field"))


def _structural_evidence_scores(
    graph: EvidenceGraph,
    field_nodes: tuple[Node, ...],
) -> list[float]:
    """Collect evidence scores from structural fields and their ``has_field`` edges."""
    scores = [evidence.score for node in field_nodes for evidence in node.evidence]
    field_ids = {node.id for node in field_nodes}
    for edge in edges_with_label(graph, "has_field"):
        if edge.target_id in field_ids:
            scores.extend(evidence.score for evidence in edge.evidence)
    return scores


def _structural_field_evidence(field_nodes: tuple[Node, ...]) -> tuple[Evidence, ...]:
    """Return provenance attached to structural field nodes."""
    return tuple(evidence for node in field_nodes for evidence in node.evidence)


def _build_structural_candidate(
    graph: EvidenceGraph,
    label: str,
    field_nodes: tuple[Node, ...],
) -> EntityCandidate:
    """Build a structural entity candidate from supporting field nodes."""
    slug = label.lower()
    return EntityCandidate(
        name=_title_case(slug),
        slug=slug,
        confidence=combine_scores(_structural_evidence_scores(graph, field_nodes)),
        graph_node_id=f"entity:{slug}",
        evidence=_structural_field_evidence(field_nodes),
    )


def _interface_entity(graph: EvidenceGraph) -> EntityCandidate | None:
    """Infer an ``Interface`` entity from ``interface`` field labels in the graph."""
    return _structural_entity(graph, _INTERFACE_LABEL)


def _template_id_from_field(field_node_id: str) -> str:
    _, template_id, _param = field_node_id.split(":", maxsplit=2)
    return template_id


def _hierarchy_entities(
    graph: EvidenceGraph,
    data: ProviderInput,
    min_confidence: float,
) -> tuple[EntityCandidate, ...]:
    """Promote entity slugs referenced by template-order hierarchy."""
    index = build_hierarchy_index(data)
    process_by_template = _process_slug_by_template(data)
    slugs: set[str] = set()
    for parent_slug, child_slug in index.owns_edges:
        slugs.add(parent_slug)
        slugs.add(child_slug)
    for template in data.templates:
        process_slug = process_by_template.get(template.id)
        slugs.update(ordered_entity_chain(template.template, process_slug=process_slug))
    candidates: list[EntityCandidate] = []
    for slug in sorted(slugs):
        candidate = _hierarchy_entity_candidate(graph, slug)
        if candidate is not None and candidate.confidence >= min_confidence:
            candidates.append(candidate)
    return tuple(candidates)


def _process_slug_by_template(data: ProviderInput) -> dict[str, str]:
    """Return the most common process slug for each template id."""
    counts: dict[str, Counter[str]] = {}
    for occurrence in data.occurrences:
        if occurrence.process is None:
            continue
        slug = slugify(occurrence.process)
        counts.setdefault(occurrence.template_id, Counter())[slug] += 1
    return {template_id: counter.most_common(1)[0][0] for template_id, counter in counts.items()}


def _hierarchy_entity_candidate(graph: EvidenceGraph, slug: str) -> EntityCandidate | None:
    """Build an entity candidate for a hierarchy slug when not already promoted."""
    node = graph.get_node(f"entity:{slug}")
    if node is not None:
        return _promote_entity_node(node)
    return EntityCandidate(
        name=_title_case(slug),
        slug=slug,
        confidence=0.65,
        graph_node_id=f"entity:{slug}",
        evidence=(
            Evidence(
                source="namespace",
                score=0.65,
                explanation=f"Entity {slug!r} inferred from template occurrence order",
            ),
        ),
    )


def _title_case(slug: str) -> str:
    return slug.replace("_", " ").title()


def _event_noun_entities(
    graph: EvidenceGraph,
    min_confidence: float,
) -> tuple[EntityCandidate, ...]:
    """Infer entities from shared event noun prefixes."""
    grouped = _group_event_nodes_by_noun(graph)
    candidates: list[EntityCandidate] = []
    for noun, nodes in grouped.items():
        candidate = _event_noun_candidate(noun, nodes)
        if candidate is not None and candidate.confidence >= min_confidence:
            candidates.append(candidate)
    return tuple(candidates)


def _group_event_nodes_by_noun(graph: EvidenceGraph) -> dict[str, list[Node]]:
    """Group event nodes by extracted noun prefix."""
    grouped: dict[str, list[Node]] = {}
    for node in nodes_by_kind(graph, NodeKind.EVENT):
        noun = event_noun_from_slug(node.id.removeprefix("event:"))
        if noun is None:
            continue
        grouped.setdefault(noun, []).append(node)
    return grouped


def _event_noun_candidate(noun: str, nodes: list[Node]) -> EntityCandidate | None:
    """Build an entity candidate when enough events share a noun prefix."""
    if len(nodes) < _MIN_EVENT_NOUN_EVENTS:
        return None
    evidence = tuple(item for node in nodes for item in collect_evidence(node))
    return EntityCandidate(
        name=_title_case(noun),
        slug=noun,
        confidence=combine_scores([item.score for item in evidence]),
        graph_node_id=f"entity:{noun}",
        evidence=evidence,
    )
