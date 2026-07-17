"""Tests for ontolog.models.domain."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ontolog.models.domain import (
    Alternative,
    Entity,
    Field,
    ProbabilisticClaim,
    ProbabilisticDomainModel,
)
from ontolog.models.evidence import Evidence


def _sample_evidence() -> Evidence:
    return Evidence(source="regex", score=0.9, explanation="IPv4 pattern")


def test_probabilistic_domain_model_json_round_trip() -> None:
    claim = ProbabilisticClaim(
        value="ipv4",
        confidence=0.95,
        evidence=(_sample_evidence(),),
        export_eligible=True,
    )
    model = ProbabilisticDomainModel(
        entities=(),
        events=(),
        fields=(Field(name="destination", type_name=claim, graph_node_id="field:destination"),),
        relationships=(),
        state_machines=(),
    )
    restored = ProbabilisticDomainModel.model_validate_json(model.model_dump_json())
    assert restored == model


def test_probabilistic_domain_model_frozen() -> None:
    claim = ProbabilisticClaim(
        value="ipv4",
        confidence=0.95,
        evidence=(_sample_evidence(),),
        export_eligible=True,
    )
    model = ProbabilisticDomainModel(
        fields=(Field(name="destination", type_name=claim, graph_node_id="field:destination"),),
    )
    with pytest.raises(ValidationError):
        model.schema_version = "2"  # type: ignore[misc]


def test_entity_claim_includes_evidence_when_confident() -> None:
    entity = Entity(
        name="ControlBoard",
        slug="control-board",
        confidence=0.8,
        evidence=(_sample_evidence(),),
        export_eligible=True,
    )
    assert entity.confidence > 0
    assert entity.evidence


def test_field_type_claim_includes_evidence_when_confident() -> None:
    claim = ProbabilisticClaim(
        value="hex",
        confidence=0.95,
        evidence=(_sample_evidence(),),
        export_eligible=True,
    )
    field = Field(name="payload", type_name=claim, graph_node_id="field:payload")
    assert field.type_name.confidence > 0
    assert field.type_name.evidence


def test_alternative_construct() -> None:
    alternative = Alternative(
        value="string",
        confidence=0.6,
        evidence=(_sample_evidence(),),
    )
    assert alternative.value == "string"
