"""Tests for ontolog.models.evidence."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ontolog.models.evidence import Edge, Evidence, Node, NodeKind


def test_evidence_construct_minimal() -> None:
    evidence = Evidence(source="regex", score=0.9, explanation="IPv4 pattern")
    assert evidence.source == "regex"
    assert evidence.score == 0.9
    assert evidence.explanation == "IPv4 pattern"
    assert evidence.samples == ()


def test_evidence_score_bounds() -> None:
    with pytest.raises(ValidationError):
        Evidence(source="regex", score=1.5, explanation="too high")
    with pytest.raises(ValidationError):
        Evidence(source="regex", score=-0.1, explanation="too low")


def test_evidence_construct_full() -> None:
    evidence = Evidence(
        source="stats",
        score=0.5,
        explanation="frequency",
        samples=("line1", "line2"),
    )
    assert evidence.samples == ("line1", "line2")


def test_evidence_frozen() -> None:
    evidence = Evidence(source="regex", score=0.9, explanation="pattern")
    with pytest.raises(ValidationError):
        evidence.source = "changed"  # type: ignore[misc]


def test_evidence_json_round_trip() -> None:
    original = Evidence(
        source="regex",
        score=0.95,
        explanation="IPv4 pattern",
        samples=("192.168.1.1",),
    )
    restored = Evidence.model_validate_json(original.model_dump_json())
    assert restored == original


def test_node_kind_values() -> None:
    assert {kind.name for kind in NodeKind} == {
        "ENTITY",
        "FIELD",
        "EVENT",
        "TYPE",
        "STATE",
        "RELATIONSHIP",
    }


def test_node_kind_str_enum() -> None:
    assert NodeKind.ENTITY == "entity"
    assert NodeKind.FIELD == "field"


def test_node_construct_minimal() -> None:
    node = Node(id="entity:controlboard", kind=NodeKind.ENTITY, label="ControlBoard")
    assert node.id == "entity:controlboard"
    assert node.kind is NodeKind.ENTITY
    assert node.label == "ControlBoard"
    assert node.evidence == ()


def test_node_construct_with_evidence() -> None:
    evidence = Evidence(source="namespace", score=0.8, explanation="token hierarchy")
    node = Node(
        id="entity:controlboard",
        kind=NodeKind.ENTITY,
        label="ControlBoard",
        evidence=(evidence,),
    )
    assert len(node.evidence) == 1
    assert node.evidence[0] == evidence


def test_node_frozen() -> None:
    node = Node(id="n1", kind=NodeKind.EVENT, label="PacketSent")
    with pytest.raises(ValidationError):
        node.label = "changed"  # type: ignore[misc]


def test_node_json_round_trip() -> None:
    evidence = Evidence(source="regex", score=0.9, explanation="pattern")
    original = Node(
        id="entity:controlboard",
        kind=NodeKind.ENTITY,
        label="ControlBoard",
        evidence=(evidence,),
    )
    restored = Node.model_validate_json(original.model_dump_json())
    assert restored == original


def test_edge_construct_minimal() -> None:
    edge = Edge(source_id="entity:a", target_id="field:b")
    assert edge.source_id == "entity:a"
    assert edge.target_id == "field:b"
    assert edge.label is None
    assert edge.evidence == ()


def test_edge_construct_with_evidence() -> None:
    evidence = Evidence(source="co-occurrence", score=0.7, explanation="shared template")
    edge = Edge(
        source_id="entity:a",
        target_id="entity:b",
        label="owns",
        evidence=(evidence,),
    )
    assert edge.label == "owns"
    assert edge.evidence == (evidence,)


def test_edge_frozen() -> None:
    edge = Edge(source_id="a", target_id="b")
    with pytest.raises(ValidationError):
        edge.label = "changed"  # type: ignore[misc]


def test_edge_json_round_trip() -> None:
    evidence = Evidence(source="regex", score=0.9, explanation="pattern")
    original = Edge(
        source_id="entity:a",
        target_id="entity:b",
        label="owns",
        evidence=(evidence,),
    )
    restored = Edge.model_validate_json(original.model_dump_json())
    assert restored == original
