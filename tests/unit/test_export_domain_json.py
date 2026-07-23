"""Tests for domain-json export."""

from __future__ import annotations

import json
from pathlib import Path

from helpers import aggregate_fixture
from ontolog.config import ConfidenceThresholds, OntologConfig
from ontolog.export.formats import ExportFormat
from ontolog.export.options import ExportOptions
from ontolog.export.registry import export_domain_model
from ontolog.models.domain import Entity, ProbabilisticDomainModel

EXPORT_CONFIG = OntologConfig(confidence=ConfidenceThresholds(export=0.6))


def test_domain_json_round_trips(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path, config=EXPORT_CONFIG)
    artifact = export_domain_model(model, ExportFormat.DOMAIN_JSON)
    restored = ProbabilisticDomainModel.model_validate(json.loads(artifact))
    assert restored == model


def test_domain_json_bypasses_filtering() -> None:
    model = ProbabilisticDomainModel(
        entities=(
            Entity(
                name="Hidden",
                slug="hidden",
                confidence=0.1,
                evidence=(),
                export_eligible=False,
            ),
        ),
    )
    artifact = export_domain_model(model, ExportFormat.DOMAIN_JSON, options=ExportOptions())
    payload = json.loads(artifact)
    assert len(payload["entities"]) == 1
    assert payload["entities"][0]["name"] == "Hidden"
