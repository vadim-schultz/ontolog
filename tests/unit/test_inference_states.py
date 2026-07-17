"""Tests for state machine inference."""

from __future__ import annotations

from pathlib import Path

from helpers import infer_fixture, load_fixture_graph
from ontolog.config import default_config
from ontolog.inference.runner import run_inference
from ontolog.inference.states import StateInferencePass


def test_lifecycle_states_detected(tmp_path: Path) -> None:
    graph, data = load_fixture_graph("order_lifecycle.log", tmp_path)
    result = run_inference(
        graph,
        data,
        (StateInferencePass(),),
        thresholds=default_config().confidence,
    )
    machine = result.state_machines[0]
    assert set(machine.states) >= {"created", "validated", "running", "completed"}


def test_transition_sequence(tmp_path: Path) -> None:
    graph, data = load_fixture_graph("order_lifecycle.log", tmp_path)
    result = run_inference(
        graph,
        data,
        (StateInferencePass(),),
        thresholds=default_config().confidence,
    )
    pairs = {(t.from_state, t.to_state) for t in result.state_machines[0].transitions}
    assert ("created", "validated") in pairs
    assert ("validated", "running") in pairs
    assert ("running", "completed") in pairs


def test_transition_counts(tmp_path: Path) -> None:
    graph, data = load_fixture_graph("order_lifecycle.log", tmp_path)
    result = run_inference(
        graph,
        data,
        (StateInferencePass(),),
        thresholds=default_config().confidence,
    )
    transitions = result.state_machines[0].transitions
    assert all(transition.count >= 3 for transition in transitions)


def test_state_machine_confidence(tmp_path: Path) -> None:
    graph, data = load_fixture_graph("order_lifecycle.log", tmp_path)
    result = run_inference(
        graph,
        data,
        (StateInferencePass(),),
        thresholds=default_config().confidence,
    )
    assert result.state_machines[0].confidence >= 0.6


def test_no_states_from_controlboard(tmp_path: Path) -> None:
    result = infer_fixture("controlboard.log", tmp_path)
    assert result.state_machines == ()
