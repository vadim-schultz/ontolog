"""SQLite persistence for mined templates."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import cast

from ontolog.errors import StorageError
from ontolog.models.template import Template, TemplateOccurrence, TemplateParameter
from ontolog.storage import queries

_SCHEMA_VERSION = 1


def _encode_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _decode_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


def _merge_examples(
    existing: tuple[str, ...], incoming: tuple[str, ...], *, cap: int = 5
) -> tuple[str, ...]:
    merged: list[str] = []
    for example in (*existing, *incoming):
        if example not in merged:
            merged.append(example)
        if len(merged) >= cap:
            break
    return tuple(merged)


def _merge_datetimes(
    existing: datetime | None,
    incoming: datetime | None,
    *,
    pick_min: bool,
) -> datetime | None:
    if existing is None:
        return incoming
    if incoming is None:
        return existing
    return min(existing, incoming) if pick_min else max(existing, incoming)


def _template_from_row(row: sqlite3.Row) -> Template:
    return Template(
        id=row["id"],
        template=row["template"],
        occurrence_count=row["occurrence_count"],
        first_seen=_decode_datetime(row["first_seen"]),
        last_seen=_decode_datetime(row["last_seen"]),
        examples=tuple(json.loads(row["examples"])),
    )


def _template_insert_params(template: Template) -> tuple[str | int | None, ...]:
    return (
        template.id,
        template.template,
        template.occurrence_count,
        _encode_datetime(template.first_seen),
        _encode_datetime(template.last_seen),
        json.dumps(list(template.examples)),
    )


def _template_update_params(template: Template) -> tuple[str | int | None, ...]:
    return (
        template.occurrence_count,
        _encode_datetime(template.first_seen),
        _encode_datetime(template.last_seen),
        json.dumps(list(template.examples)),
        template.id,
    )


def _occurrence_from_row(row: sqlite3.Row) -> TemplateOccurrence:
    raw_params = json.loads(row["parameters"])
    parameters = tuple(
        TemplateParameter(name=item["name"], value=item["value"]) for item in raw_params
    )
    return TemplateOccurrence(
        template_id=row["template_id"],
        timestamp=_decode_datetime(row["timestamp"]),
        message=row["message"],
        parameters=parameters,
        process=row["process"],
    )


def _occurrence_insert_params(occurrence: TemplateOccurrence) -> tuple[str | None, ...]:
    return (
        occurrence.template_id,
        _encode_datetime(occurrence.timestamp),
        occurrence.message,
        json.dumps([{"name": param.name, "value": param.value} for param in occurrence.parameters]),
        occurrence.process,
    )


def _merge_stored_template(existing: sqlite3.Row, incoming: Template) -> Template:
    return Template(
        id=existing["id"],
        template=existing["template"],
        occurrence_count=existing["occurrence_count"] + incoming.occurrence_count,
        first_seen=_merge_datetimes(
            _decode_datetime(existing["first_seen"]),
            incoming.first_seen,
            pick_min=True,
        ),
        last_seen=_merge_datetimes(
            _decode_datetime(existing["last_seen"]),
            incoming.last_seen,
            pick_min=False,
        ),
        examples=_merge_examples(
            tuple(json.loads(existing["examples"])),
            incoming.examples,
        ),
    )


class SqliteTemplateStore:
    """Persist templates and occurrences in a local SQLite database."""

    def __init__(self, path: Path) -> None:
        self._path = path
        try:
            self._connection = sqlite3.connect(path)
        except sqlite3.Error as exc:
            raise StorageError(f"failed to open database: {exc}", path=path) from exc
        self._connection.row_factory = sqlite3.Row
        self._initialize()

    @property
    def path(self) -> Path:
        return self._path

    def _initialize(self) -> None:
        try:
            self._connection.executescript(queries.CREATE_SCHEMA)
            self._connection.commit()
        except sqlite3.Error as exc:
            raise StorageError(f"failed to initialize schema: {exc}", path=self._path) from exc
        try:
            self._connection.execute(queries.MIGRATE_ADD_PROCESS_COLUMN)
            self._connection.commit()
        except sqlite3.Error:
            pass

    def upsert_template(self, template: Template) -> None:
        """Insert or merge a template row."""
        try:
            existing = self._find_template_row(template)
            if existing is None:
                self._insert_template_row(template)
            else:
                self._update_template_row(_merge_stored_template(existing, template))
            self._connection.commit()
        except sqlite3.Error as exc:
            message = f"failed to upsert template: {exc}"
            raise StorageError(message, path=self._path) from exc

    def _find_template_row(self, template: Template) -> sqlite3.Row | None:
        row = self._connection.execute(
            queries.FIND_TEMPLATE_BY_ID_OR_TEXT,
            (template.id, template.template),
        ).fetchone()
        return cast("sqlite3.Row | None", row)

    def _insert_template_row(self, template: Template) -> None:
        self._connection.execute(
            queries.INSERT_TEMPLATE,
            _template_insert_params(template),
        )

    def _update_template_row(self, template: Template) -> None:
        self._connection.execute(
            queries.UPDATE_TEMPLATE,
            _template_update_params(template),
        )

    def _insert_occurrence_row(self, occurrence: TemplateOccurrence) -> None:
        self._connection.execute(
            queries.INSERT_OCCURRENCE,
            _occurrence_insert_params(occurrence),
        )

    def insert_occurrence(self, occurrence: TemplateOccurrence) -> None:
        """Insert one template occurrence row."""
        try:
            self._insert_occurrence_row(occurrence)
            self._connection.commit()
        except sqlite3.Error as exc:
            message = f"failed to insert occurrence: {exc}"
            raise StorageError(message, path=self._path) from exc

    def list_templates(self) -> list[Template]:
        """Return all stored templates."""
        try:
            rows = self._connection.execute(queries.LIST_TEMPLATES).fetchall()
        except sqlite3.Error as exc:
            message = f"failed to list templates: {exc}"
            raise StorageError(message, path=self._path) from exc

        return [_template_from_row(row) for row in rows]

    def list_occurrences(self, *, template_id: str | None = None) -> list[TemplateOccurrence]:
        """Return stored template occurrences, optionally filtered by template id."""
        try:
            if template_id is None:
                rows = self._connection.execute(queries.LIST_OCCURRENCES).fetchall()
            else:
                rows = self._connection.execute(
                    queries.LIST_OCCURRENCES_BY_TEMPLATE,
                    (template_id,),
                ).fetchall()
        except sqlite3.Error as exc:
            message = f"failed to list occurrences: {exc}"
            raise StorageError(message, path=self._path) from exc

        return [_occurrence_from_row(row) for row in rows]

    def resolve_template_id(self, template_text: str) -> str | None:
        """Return the stored template id for a mined template string, if present."""
        try:
            row = self._connection.execute(
                queries.RESOLVE_TEMPLATE_ID,
                (template_text,),
            ).fetchone()
        except sqlite3.Error as exc:
            message = f"failed to resolve template id: {exc}"
            raise StorageError(message, path=self._path) from exc
        if row is None:
            return None
        return str(row["id"])

    def close(self) -> None:
        """Close the database connection."""
        self._connection.close()

    def __enter__(self) -> SqliteTemplateStore:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
