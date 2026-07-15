"""Tests for ontolog.config."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from ontolog.config import ConfidenceThresholds, MaskKind, OntologConfig, default_config


def test_default_config() -> None:
    config = default_config()
    assert config.masks.enabled == frozenset(MaskKind)
    assert config.confidence.export == 0.7
    assert config.confidence.field == 0.5
    assert config.confidence.entity == 0.6
    assert config.confidence.relationship == 0.6
    assert config.confidence.event == 0.5
    assert config.storage_path == Path("ontolog.db")


def test_custom_masks() -> None:
    config = OntologConfig(masks={"enabled": [MaskKind.IP, MaskKind.UUID]})
    assert config.masks.enabled == frozenset({MaskKind.IP, MaskKind.UUID})


def test_threshold_bounds() -> None:
    with pytest.raises(ValidationError):
        ConfidenceThresholds(export=1.1)


def test_storage_path() -> None:
    config = OntologConfig(storage_path="custom.db")
    assert config.storage_path == Path("custom.db")


def test_frozen() -> None:
    config = default_config()
    with pytest.raises(ValidationError):
        config.storage_path = Path("other.db")  # type: ignore[misc]
