"""Tests for NamespaceProvider."""

from __future__ import annotations

from ontolog.evidence.graph import EvidenceGraph
from ontolog.evidence.runner import run_providers
from ontolog.models.finding import ProviderInput
from ontolog.models.template import Template, TemplateOccurrence, TemplateParameter
from ontolog.providers.namespace import NamespaceProvider


def test_process_name_yields_entity() -> None:
    data = ProviderInput(
        occurrences=(
            TemplateOccurrence(
                template_id="cluster_1",
                message="PacketSent interface=eth0",
                parameters=(TemplateParameter(name="interface", value="eth0"),),
                process="controlboard",
            ),
        ),
    )
    graph = EvidenceGraph()
    run_providers(graph, data, (NamespaceProvider(),))
    assert graph.get_node("entity:controlboard") is not None


def test_token_pairs_yield_hierarchy() -> None:
    data = ProviderInput(
        templates=(Template(id="cluster_1", template="PacketSent interface=<*> destination=<IP>"),),
        occurrences=(
            TemplateOccurrence(
                template_id="cluster_1",
                message="PacketSent interface=eth0 destination=192.168.1.1",
                parameters=(
                    TemplateParameter(name="interface", value="eth0"),
                    TemplateParameter(name="destination", value="192.168.1.1"),
                ),
                process="controlboard",
            ),
        ),
    )
    graph = EvidenceGraph()
    run_providers(graph, data, (NamespaceProvider(),))
    assert graph.get_node("event:packetsent") is not None


def test_interface_field_linked_to_entity() -> None:
    data = ProviderInput(
        templates=(Template(id="cluster_1", template="PacketSent interface=<*>"),),
        occurrences=(
            TemplateOccurrence(
                template_id="cluster_1",
                message="PacketSent interface=eth0",
                parameters=(TemplateParameter(name="interface", value="eth0"),),
                process="controlboard",
            ),
        ),
    )
    graph = EvidenceGraph()
    run_providers(graph, data, (NamespaceProvider(),))
    edges = [edge for edge in graph.edges() if edge.label == "has_field"]
    assert edges
    assert edges[0].source_id == "entity:controlboard"
