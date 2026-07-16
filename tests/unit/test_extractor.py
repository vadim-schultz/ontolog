"""Tests for ontolog.templates.extractor."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from ontolog.models import LogRecord
from ontolog.templates.extractor import ExtractOptions, TemplateExtractor, extract_templates

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
FIXTURE_LINE = "PacketSent interface=eth0 destination=192.168.1.10 payload=0xdeadbeef"


def test_single_record_returns_template() -> None:
    extractor = TemplateExtractor()
    record = LogRecord(message=FIXTURE_LINE, timestamp=datetime(2024, 1, 15, tzinfo=UTC))
    template = extractor.ingest(record)

    assert template is not None
    assert template.occurrence_count == 1
    assert template.id.startswith("cluster_")
    assert template.template


def test_same_pattern_increments_count() -> None:
    extractor = TemplateExtractor()
    first = LogRecord(message=FIXTURE_LINE)
    second = LogRecord(
        message="PacketSent interface=eth0 destination=192.168.1.11 payload=0xdeadbef0"
    )

    extractor.ingest(first)
    template = extractor.ingest(second)

    assert template is not None
    assert len(extractor.templates()) == 1
    assert template.occurrence_count == 2


def test_controlboard_parameters_extracted() -> None:
    extractor = TemplateExtractor()
    first = LogRecord(message=FIXTURE_LINE)
    second = LogRecord(
        message="PacketSent interface=eth0 destination=192.168.1.11 payload=0xdeadbef0"
    )
    extractor.ingest(first)
    template = extractor.ingest(second)

    assert template is not None
    assert "<IP>" in template.template
    assert "<HEX>" in template.template


def test_empty_message_skipped() -> None:
    extractor = TemplateExtractor()
    result = extractor.ingest(LogRecord(message="   "))

    assert result is None
    assert extractor.templates() == []


def test_templates_sorted_by_count() -> None:
    templates = extract_templates(FIXTURES / "controlboard.log", ExtractOptions())

    assert templates
    counts = [template.occurrence_count for template in templates]
    assert counts == sorted(counts, reverse=True)
