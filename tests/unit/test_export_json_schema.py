"""Tests for JSON Schema export."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from helpers import aggregate_fixture
from ontolog.config import ConfidenceThresholds, OntologConfig
from ontolog.export.formats import ExportFormat
from ontolog.export.registry import export_domain_model

EXPORT_CONFIG = OntologConfig(confidence=ConfidenceThresholds(export=0.6))


def test_schema_has_entity_definitions(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path, config=EXPORT_CONFIG)
    schema = json.loads(export_domain_model(model, ExportFormat.JSON_SCHEMA))
    properties = schema["properties"]
    assert "Controlboard" in properties
    assert "Interface" in properties


def test_schema_field_types(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path, config=EXPORT_CONFIG)
    schema = json.loads(export_domain_model(model, ExportFormat.JSON_SCHEMA))
    destination = schema["properties"]["destination"]
    payload = schema["properties"]["payload"]
    assert destination["format"] == "ipv4"
    assert "pattern" in payload


def test_schema_omits_ineligible(tmp_path: Path) -> None:
    strict = OntologConfig(confidence=ConfidenceThresholds(export=0.99))
    model = aggregate_fixture("controlboard.log", tmp_path, config=strict)
    schema = json.loads(export_domain_model(model, ExportFormat.JSON_SCHEMA))
    properties = schema.get("properties", {})
    assert "Controlboard" not in properties
    assert "Interface" not in properties


def test_sample_instance_validates(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path, config=EXPORT_CONFIG)
    schema = json.loads(export_domain_model(model, ExportFormat.JSON_SCHEMA))
    sample = {
        "Controlboard": {},
        "Interface": {},
        "destination": "10.0.0.1",
        "payload": "deadbeef",
    }
    jsonschema.validate(sample, schema)
