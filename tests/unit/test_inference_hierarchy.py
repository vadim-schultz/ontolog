"""Tests for order-of-occurrence hierarchy inference."""

from __future__ import annotations

from pathlib import Path

from helpers import load_fixture_graph
from ontolog.config import default_config
from ontolog.inference.hierarchy import (
    STRUCTURAL_FIELD_LABELS,
    build_hierarchy_index,
    ordered_entity_chain,
    owner_slug_for_field,
)
from ontolog.inference.relationships import RelationshipInferencePass
from ontolog.inference.runner import run_inference
from ontolog.models.template import Template


def test_ordered_entity_chain_controlboard_packet_sent() -> None:
    chain = ordered_entity_chain(
        "PacketSent interface=eth0 destination=<IP> payload=<HEX>",
        process_slug="controlboard",
    )
    assert chain == ("controlboard", "packet", "interface")


def test_ordered_entity_chain_connection_established() -> None:
    chain = ordered_entity_chain(
        "ConnectionEstablished interface=eth0 peer=<IP>",
        process_slug="controlboard",
    )
    assert chain == ("controlboard", "connection", "interface")


def test_owner_slug_for_destination_on_interface() -> None:
    owner = owner_slug_for_field(
        "PacketSent interface=eth0 destination=<IP> payload=<HEX>",
        "destination",
        process_slug="controlboard",
    )
    assert owner == "interface"


def test_owner_slug_for_peer_on_interface() -> None:
    owner = owner_slug_for_field(
        "ConnectionEstablished interface=eth0 peer=<IP>",
        "peer",
        process_slug="controlboard",
    )
    assert owner == "interface"


def test_structural_field_labels_include_interface() -> None:
    assert "interface" in STRUCTURAL_FIELD_LABELS


def test_build_hierarchy_index_owns_chain(tmp_path: Path) -> None:
    _, data = load_fixture_graph("controlboard.log", tmp_path)
    index = build_hierarchy_index(data)
    assert ("controlboard", "packet") in index.owns_edges
    assert ("packet", "interface") in index.owns_edges
    assert ("controlboard", "connection") in index.owns_edges
    assert ("connection", "interface") in index.owns_edges


def test_build_hierarchy_index_field_owners(tmp_path: Path) -> None:
    _, data = load_fixture_graph("controlboard.log", tmp_path)
    index = build_hierarchy_index(data)
    sent_template = next(
        template for template in data.templates if template.template.startswith("PacketSent")
    )
    assert index.field_owner(sent_template.id, "destination") == "interface"
    assert index.field_owner(sent_template.id, "payload") == "interface"


def test_deep_chain_three_entity_levels() -> None:
    """Process -> event noun -> structural field spans three entity levels."""
    template = Template(
        id="deep_1",
        template="PacketSent segment=seg0 interface=eth0 destination=<IP>",
    )
    chain = ordered_entity_chain(template.template, process_slug="router")
    assert len(chain) == 4
    assert chain[0] == "router"
    assert chain[1] == "packet"
    assert chain[-1] == "interface"


def test_chained_owns_relationships(tmp_path: Path) -> None:
    graph, data = load_fixture_graph("controlboard.log", tmp_path)
    result = run_inference(
        graph,
        data,
        (RelationshipInferencePass(),),
        thresholds=default_config().confidence,
    )
    owns = {
        (relationship.source_name, relationship.target_name)
        for relationship in result.relationships
        if relationship.kind == "owns"
    }
    assert ("Controlboard", "Packet") in owns
    assert ("Packet", "Interface") in owns
    assert ("Controlboard", "Interface") not in owns
