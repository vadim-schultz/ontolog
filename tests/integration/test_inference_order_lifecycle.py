"""Integration tests for inference on order lifecycle fixture."""

from __future__ import annotations

from pathlib import Path

from helpers import infer_fixture


def test_order_lifecycle_state_machine(tmp_path: Path) -> None:
    result = infer_fixture("order_lifecycle.log", tmp_path)
    assert result.state_machines
    machine = result.state_machines[0]
    assert set(machine.states) >= {"created", "validated", "running", "completed"}
    pairs = {(transition.from_state, transition.to_state) for transition in machine.transitions}
    assert ("created", "validated") in pairs
    assert ("validated", "running") in pairs
    assert ("running", "completed") in pairs
