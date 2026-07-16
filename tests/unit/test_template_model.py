"""Tests for ontolog.models.template."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from ontolog.models.template import Template, TemplateOccurrence, TemplateParameter


def test_construct_minimal() -> None:
    template = Template(id="cluster_1", template="PacketSent interface=eth0")
    assert template.id == "cluster_1"
    assert template.template == "PacketSent interface=eth0"
    assert template.occurrence_count == 1
    assert template.first_seen is None
    assert template.last_seen is None
    assert template.examples == ()


def test_construct_full() -> None:
    first = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
    last = datetime(2024, 1, 15, 12, 1, 0, tzinfo=UTC)
    template = Template(
        id="cluster_42",
        template="PacketSent destination=<IP> payload=<HEX>",
        occurrence_count=10,
        first_seen=first,
        last_seen=last,
        examples=("msg one", "msg two"),
    )
    assert template.occurrence_count == 10
    assert template.first_seen == first
    assert template.last_seen == last
    assert template.examples == ("msg one", "msg two")


def test_occurrence_count_validation() -> None:
    with pytest.raises(ValidationError):
        Template(id="cluster_1", template="hello", occurrence_count=0)


def test_frozen() -> None:
    template = Template(id="cluster_1", template="hello")
    with pytest.raises(ValidationError):
        template.template = "changed"  # type: ignore[misc]


def test_json_round_trip() -> None:
    first = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
    original = Template(
        id="cluster_1",
        template="PacketSent destination=<IP>",
        occurrence_count=3,
        first_seen=first,
        examples=("example",),
    )
    restored = Template.model_validate_json(original.model_dump_json())
    assert restored == original


def test_template_parameter() -> None:
    param = TemplateParameter(name="IP", value="192.168.1.1")
    assert param.name == "IP"
    assert param.value == "192.168.1.1"


def test_template_occurrence() -> None:
    timestamp = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
    occurrence = TemplateOccurrence(
        template_id="cluster_1",
        timestamp=timestamp,
        message="PacketSent destination=192.168.1.1",
        parameters=(TemplateParameter(name="IP", value="192.168.1.1"),),
    )
    assert occurrence.template_id == "cluster_1"
    assert occurrence.timestamp == timestamp
    assert len(occurrence.parameters) == 1
