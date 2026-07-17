"""Integration tests for inference on controlboard fixture."""

from __future__ import annotations

from pathlib import Path

from helpers import infer_fixture


def test_controlboard_inference_mvp(tmp_path: Path) -> None:
    result = infer_fixture("controlboard.log", tmp_path)
    entity_slugs = {entity.slug for entity in result.entities}
    event_slugs = {event.slug for event in result.events}
    assert entity_slugs >= {"controlboard", "interface"}
    assert "packetsent" in event_slugs or any("sent" in slug for slug in event_slugs)
    assert "packetreceived" in event_slugs or any("received" in slug for slug in event_slugs)
    assert "connectionestablished" in event_slugs or any(
        "established" in slug for slug in event_slugs
    )

    destination = next(field for field in result.fields if field.name == "destination")
    payload = next(field for field in result.fields if field.name == "payload")
    assert destination.type_name == "ipv4" and destination.confidence >= 0.95
    assert payload.type_name == "hex" and payload.confidence >= 0.95

    owns = next(
        relationship for relationship in result.relationships if relationship.kind == "owns"
    )
    assert owns.source_name == "Controlboard"
    assert owns.target_name == "Interface"
