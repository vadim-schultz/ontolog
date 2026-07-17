"""Tests for event inference."""

from __future__ import annotations

from pathlib import Path

from helpers import load_fixture_graph
from ontolog.config import default_config
from ontolog.evidence.graph import EvidenceGraph
from ontolog.inference.events import EventInferencePass
from ontolog.inference.runner import run_inference
from ontolog.models.finding import ProviderInput


def test_packet_sent_verbs(tmp_path: Path) -> None:
    graph, data = load_fixture_graph("controlboard.log", tmp_path)
    result = run_inference(
        graph,
        data,
        (EventInferencePass(),),
        thresholds=default_config().confidence,
    )
    packet_sent = next(event for event in result.events if "sent" in event.slug)
    assert "send" in packet_sent.verbs


def test_packet_received_verbs(tmp_path: Path) -> None:
    graph, data = load_fixture_graph("controlboard.log", tmp_path)
    result = run_inference(
        graph,
        data,
        (EventInferencePass(),),
        thresholds=default_config().confidence,
    )
    packet_received = next(event for event in result.events if "received" in event.slug)
    assert "receive" in packet_received.verbs


def test_connection_established_verbs(tmp_path: Path) -> None:
    graph, data = load_fixture_graph("controlboard.log", tmp_path)
    result = run_inference(
        graph,
        data,
        (EventInferencePass(),),
        thresholds=default_config().confidence,
    )
    connection = next(event for event in result.events if "established" in event.slug)
    assert "connect" in connection.verbs


def test_lifecycle_create_verb(tmp_path: Path) -> None:
    graph, data = load_fixture_graph("order_lifecycle.log", tmp_path)
    result = run_inference(
        graph,
        data,
        (EventInferencePass(),),
        thresholds=default_config().confidence,
    )
    created = next(event for event in result.events if "created" in event.slug)
    assert "create" in created.verbs


def test_frequency_boosts_confidence(tmp_path: Path) -> None:
    graph, data = load_fixture_graph("controlboard.log", tmp_path)
    result = run_inference(
        graph,
        data,
        (EventInferencePass(),),
        thresholds=default_config().confidence,
    )
    assert all(event.confidence >= 0.75 for event in result.events)


def test_non_event_nodes_ignored() -> None:
    graph = EvidenceGraph()
    result = run_inference(
        graph,
        ProviderInput(),
        (EventInferencePass(),),
        thresholds=default_config().confidence,
    )
    assert result.events == ()
