"""Integration tests for deeply nested hierarchy fixture."""

from __future__ import annotations

from pathlib import Path

from helpers import infer_fixture


def test_nested_hierarchy_four_entity_levels(tmp_path: Path) -> None:
    result = infer_fixture("nested_hierarchy.log", tmp_path)
    owns = {
        (relationship.source_name, relationship.target_name)
        for relationship in result.relationships
        if relationship.kind == "owns"
    }
    assert ("Router", "Packet") in owns
    assert ("Packet", "Segment") in owns
    assert ("Segment", "Interface") in owns
    destination = next(field for field in result.fields if field.name == "destination")
    assert destination.entity_slug == "interface"
