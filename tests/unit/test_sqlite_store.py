"""Tests for ontolog.storage.sqlite."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from ontolog.errors import StorageError
from ontolog.models.template import Template, TemplateOccurrence, TemplateParameter
from ontolog.storage.sqlite import SqliteTemplateStore


def test_upsert_and_list(tmp_path: Path) -> None:
    store = SqliteTemplateStore(tmp_path / "test.db")
    template = Template(
        id="cluster_1",
        template="PacketSent destination=<IP>",
        occurrence_count=2,
        examples=("one",),
    )
    store.upsert_template(template)

    templates = store.list_templates()
    store.close()

    assert len(templates) == 1
    assert templates[0] == template


def test_insert_occurrence(tmp_path: Path) -> None:
    store = SqliteTemplateStore(tmp_path / "test.db")
    store.upsert_template(Template(id="cluster_1", template="hello"))
    store.insert_occurrence(
        TemplateOccurrence(
            template_id="cluster_1",
            message="hello world",
            parameters=(TemplateParameter(name="*", value="world"),),
        )
    )
    row = store._connection.execute("SELECT COUNT(*) FROM template_occurrences").fetchone()
    store.close()
    assert row is not None
    assert row[0] == 1


def test_reload_in_new_instance(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    store = SqliteTemplateStore(db_path)
    store.upsert_template(Template(id="cluster_1", template="hello", occurrence_count=3))
    store.close()

    reloaded = SqliteTemplateStore(db_path)
    templates = reloaded.list_templates()
    reloaded.close()

    assert templates[0].occurrence_count == 3


def test_upsert_merges_counts_and_timestamps(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    first_seen = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
    later = datetime(2024, 1, 15, 13, 0, 0, tzinfo=UTC)

    store = SqliteTemplateStore(db_path)
    store.upsert_template(
        Template(
            id="cluster_1",
            template="PacketSent destination=<IP>",
            occurrence_count=2,
            first_seen=first_seen,
            last_seen=first_seen,
            examples=("one",),
        )
    )
    store.upsert_template(
        Template(
            id="cluster_99",
            template="PacketSent destination=<IP>",
            occurrence_count=3,
            first_seen=later,
            last_seen=later,
            examples=("two", "three"),
        )
    )
    templates = store.list_templates()
    store.close()

    assert len(templates) == 1
    assert templates[0].id == "cluster_1"
    assert templates[0].occurrence_count == 5
    assert templates[0].first_seen == first_seen
    assert templates[0].last_seen == later
    assert templates[0].examples == ("one", "two", "three")


def test_storage_error_has_path(tmp_path: Path) -> None:
    with pytest.raises(StorageError) as exc_info:
        SqliteTemplateStore(tmp_path / "blocked" / "test.db")
    assert exc_info.value.path == tmp_path / "blocked" / "test.db"
