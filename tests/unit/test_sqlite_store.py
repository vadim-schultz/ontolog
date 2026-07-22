"""Tests for ontolog.storage.sqlite."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

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
    occurrence = TemplateOccurrence(
        template_id="cluster_1",
        message="hello world",
        parameters=(TemplateParameter(name="*", value="world"),),
    )
    store.insert_occurrence(occurrence)
    store.flush()
    row = store._connection.execute("SELECT COUNT(*) FROM template_occurrences").fetchone()
    store.close()
    assert row is not None
    assert row[0] == 1


def test_list_occurrences(tmp_path: Path) -> None:
    store = SqliteTemplateStore(tmp_path / "test.db")
    store.upsert_template(Template(id="cluster_1", template="hello"))
    first = TemplateOccurrence(
        template_id="cluster_1",
        timestamp=datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC),
        message="hello one",
        parameters=(TemplateParameter(name="x", value="1"),),
    )
    second = TemplateOccurrence(
        template_id="cluster_1",
        timestamp=datetime(2024, 1, 15, 12, 0, 1, tzinfo=UTC),
        message="hello two",
        parameters=(TemplateParameter(name="x", value="2"),),
    )
    store.insert_occurrence(first)
    store.insert_occurrence(second)
    store.flush()

    all_occurrences = store.list_occurrences()
    filtered = store.list_occurrences(template_id="cluster_1")
    store.close()

    assert all_occurrences == filtered
    assert len(all_occurrences) == 2
    assert all_occurrences[0].message == "hello one"
    assert all_occurrences[1].parameters[0].value == "2"


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


def _sample_occurrence(index: int) -> TemplateOccurrence:
    return TemplateOccurrence(
        template_id="cluster_1",
        message=f"hello {index}",
        parameters=(TemplateParameter(name="x", value=str(index)),),
    )


def test_buffered_insert_occurrence_batches_writes(tmp_path: Path) -> None:
    store = SqliteTemplateStore(tmp_path / "test.db", batch_size=500)
    store.upsert_template(Template(id="cluster_1", template="hello"))

    with patch.object(store, "_flush_occurrences", wraps=store._flush_occurrences) as spy:
        for index in range(1000):
            store.insert_occurrence(_sample_occurrence(index))
        store.flush()

    assert spy.call_count == 3
    assert len(store.list_occurrences()) == 1000
    store.close()


def test_flush_writes_remaining_buffer(tmp_path: Path) -> None:
    store = SqliteTemplateStore(tmp_path / "test.db", batch_size=500)
    store.upsert_template(Template(id="cluster_1", template="hello"))
    store.insert_occurrence(_sample_occurrence(1))

    store.flush()

    assert len(store.list_occurrences()) == 1
    store.close()


def test_close_auto_flushes_buffer(tmp_path: Path) -> None:
    store = SqliteTemplateStore(tmp_path / "test.db", batch_size=500)
    store.upsert_template(Template(id="cluster_1", template="hello"))
    store.insert_occurrence(_sample_occurrence(1))
    store.close()

    reloaded = SqliteTemplateStore(tmp_path / "test.db")
    assert len(reloaded.list_occurrences()) == 1
    reloaded.close()
