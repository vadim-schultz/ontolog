"""Tests for order lifecycle pydantic export."""

from __future__ import annotations

import re
from pathlib import Path

from helpers import aggregate_fixture
from ontolog.config import ConfidenceThresholds, OntologConfig
from ontolog.export.formats import ExportFormat
from ontolog.export.registry import export_domain_model

EXPORT_CONFIG = OntologConfig(confidence=ConfidenceThresholds(export=0.6))


def test_order_lifecycle_nested_models(tmp_path: Path) -> None:
    model = aggregate_fixture("order_lifecycle.log", tmp_path, config=EXPORT_CONFIG)
    source = export_domain_model(model, ExportFormat.PYDANTIC)
    assert "class OrderStatus(StrEnum):" in source
    assert "class Order(BaseModel):" in source
    assert "class Orderservice(BaseModel):" in source
    assert "order: Order = Field(" in source
    assert re.search(
        r"status: OrderStatus = Field\(description='lifecycle status \(confidence=[0-9.]+\)'\)",
        source,
    )


def test_order_entity_inferred(tmp_path: Path) -> None:
    from helpers import infer_fixture

    result = infer_fixture("order_lifecycle.log", tmp_path, config=EXPORT_CONFIG)
    slugs = {entity.slug for entity in result.entities}
    assert "order" in slugs
    assert any(field.name == "status" for field in result.fields)
