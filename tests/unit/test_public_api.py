"""Tests for the public library API."""

from __future__ import annotations

from pathlib import Path

from helpers import FIXTURES
from ontolog import infer
from ontolog.config import default_config
from ontolog.ingestion.formats import LogFormat
from ontolog.models.domain import ProbabilisticDomainModel


def test_infer_creates_model_from_log(tmp_path: Path) -> None:
    model = infer(
        FIXTURES / "controlboard.log",
        tmp_path / "ontolog.db",
    )

    assert isinstance(model, ProbabilisticDomainModel)
    assert len(model.entities) >= 2
    assert len(model.events) >= 3


def test_infer_uses_custom_config(tmp_path: Path) -> None:
    config = default_config()
    model = infer(
        FIXTURES / "controlboard.log",
        tmp_path / "ontolog.db",
        config=config,
        format=LogFormat.PLAIN,
    )

    assert len(model.fields) >= 1


def test_infer_overwrites_existing_store(tmp_path: Path) -> None:
    store_path = tmp_path / "ontolog.db"

    first = infer(FIXTURES / "controlboard.log", store_path)
    second = infer(FIXTURES / "order_lifecycle.log", store_path)

    assert first.entities != second.entities or first.events != second.events
