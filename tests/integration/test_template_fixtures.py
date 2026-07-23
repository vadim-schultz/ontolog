"""Integration tests for template extraction on fixtures."""

from __future__ import annotations

from pathlib import Path

from ontolog.storage import SqliteTemplateStore
from ontolog.templates.extractor import ExtractOptions, extract_templates

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_controlboard_collapses_to_few_templates() -> None:
    templates = extract_templates(FIXTURES / "controlboard.log", ExtractOptions())

    assert len(templates) <= 5
    assert len(templates) >= 3
    assert all(template.occurrence_count >= 10 for template in templates)
    template_text = " ".join(template.template for template in templates)
    assert "<IP>" in template_text
    assert "<HEX>" in template_text


def test_openssh_template_count_smoke() -> None:
    # Calibrated against drain3 0.9.11 with default Ontolog mask config (observed: 23).
    templates = extract_templates(
        FIXTURES / "loghub" / "openssh_2k.log",
        ExtractOptions(),
    )

    assert 20 <= len(templates) <= 120


def test_persistence_doubles_counts(tmp_path: Path) -> None:
    db_path = tmp_path / "templates.db"
    fixture = FIXTURES / "controlboard.log"

    extract_templates(
        fixture,
        ExtractOptions(),
        store=SqliteTemplateStore(db_path),
    )
    store = SqliteTemplateStore(db_path)
    first = store.list_templates()
    first_ids = {template.id for template in first}
    first_total = sum(template.occurrence_count for template in first)
    store.close()

    extract_templates(
        fixture,
        ExtractOptions(),
        store=SqliteTemplateStore(db_path),
    )
    store = SqliteTemplateStore(db_path)
    second = store.list_templates()
    second_ids = {template.id for template in second}
    second_total = sum(template.occurrence_count for template in second)
    store.close()

    assert first_ids == second_ids
    assert second_total == first_total * 2
