"""Tests for field inference."""

from __future__ import annotations

from pathlib import Path

from helpers import load_fixture_graph
from ontolog.config import default_config
from ontolog.inference.fields import FieldInferencePass
from ontolog.inference.runner import run_inference


def test_destination_ipv4_field(tmp_path: Path) -> None:
    graph, data = load_fixture_graph("controlboard.log", tmp_path)
    result = run_inference(
        graph,
        data,
        (FieldInferencePass(),),
        thresholds=default_config().confidence,
    )
    destination = next(field for field in result.fields if field.name == "destination")
    assert destination.type_name == "ipv4"


def test_payload_hex_field(tmp_path: Path) -> None:
    graph, data = load_fixture_graph("controlboard.log", tmp_path)
    result = run_inference(
        graph,
        data,
        (FieldInferencePass(),),
        thresholds=default_config().confidence,
    )
    payload = next(field for field in result.fields if field.name == "payload")
    assert payload.type_name == "hex"


def test_destination_confidence_documented(tmp_path: Path) -> None:
    graph, data = load_fixture_graph("controlboard.log", tmp_path)
    result = run_inference(
        graph,
        data,
        (FieldInferencePass(),),
        thresholds=default_config().confidence,
    )
    destination = next(field for field in result.fields if field.name == "destination")
    assert destination.confidence >= 0.95


def test_payload_confidence_documented(tmp_path: Path) -> None:
    graph, data = load_fixture_graph("controlboard.log", tmp_path)
    result = run_inference(
        graph,
        data,
        (FieldInferencePass(),),
        thresholds=default_config().confidence,
    )
    payload = next(field for field in result.fields if field.name == "payload")
    assert payload.confidence >= 0.95


def test_untyped_field_excluded(tmp_path: Path) -> None:
    graph, data = load_fixture_graph("controlboard.log", tmp_path)
    result = run_inference(
        graph,
        data,
        (FieldInferencePass(),),
        thresholds=default_config().confidence,
    )
    field_names = {field.name for field in result.fields}
    assert "interface" not in field_names


def test_provenance_includes_regex_and_statistics(tmp_path: Path) -> None:
    graph, data = load_fixture_graph("controlboard.log", tmp_path)
    result = run_inference(
        graph,
        data,
        (FieldInferencePass(),),
        thresholds=default_config().confidence,
    )
    destination = next(field for field in result.fields if field.name == "destination")
    sources = {evidence.source for evidence in destination.evidence}
    assert "regex" in sources


def test_destination_entity_slug_controlboard(tmp_path: Path) -> None:
    graph, data = load_fixture_graph("controlboard.log", tmp_path)
    result = run_inference(
        graph,
        data,
        (FieldInferencePass(),),
        thresholds=default_config().confidence,
    )
    destination = next(field for field in result.fields if field.name == "destination")
    assert destination.entity_slug == "controlboard"


def test_star_field_excluded(tmp_path: Path) -> None:
    graph, data = load_fixture_graph("loghub/openssh_2k.log", tmp_path)
    result = run_inference(
        graph,
        data,
        (FieldInferencePass(),),
        thresholds=default_config().confidence,
    )
    field_names = {field.name for field in result.fields}
    assert "*" not in field_names
