"""Drain3-based template extraction."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig

from ontolog.config import OntologConfig, default_config
from ontolog.errors import TemplateError
from ontolog.ingestion import IngestOptions, ingest_path
from ontolog.ingestion.formats import LogFormat
from ontolog.models import LogRecord
from ontolog.models.template import Template, TemplateOccurrence, TemplateParameter
from ontolog.templates.masking import apply_mask_config

if TYPE_CHECKING:
    from ontolog.storage.sqlite import SqliteTemplateStore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _MinedMessage:
    """Drain3 mining result for one log message."""

    template_text: str
    cluster_id: str


def _cluster_id(raw_cluster_id: int | str) -> str:
    return f"cluster_{raw_cluster_id}"


def _normalized_message(record: LogRecord) -> str | None:
    message = record.message.strip()
    if message:
        return message
    logger.debug("skipping empty log message")
    return None


def _merge_examples(
    existing: tuple[str, ...],
    message: str,
    *,
    max_examples: int,
) -> tuple[str, ...]:
    if not message:
        return existing
    if existing and existing[-1] == message:
        return existing
    updated = (*existing, message)
    if len(updated) > max_examples:
        return updated[-max_examples:]
    return updated


def _min_timestamp(
    left: datetime | None,
    right: datetime | None,
) -> datetime | None:
    if left is None:
        return right
    if right is None:
        return left
    return min(left, right)


def _max_timestamp(
    left: datetime | None,
    right: datetime | None,
) -> datetime | None:
    if left is None:
        return right
    if right is None:
        return left
    return max(left, right)


def _create_miner(config: OntologConfig) -> TemplateMiner:
    """Build a Drain3 template miner from Ontolog configuration."""
    miner_config = TemplateMinerConfig()
    miner_config.drain_sim_th = 0.4
    miner_config.drain_depth = 4
    miner_config.parametrize_numeric_tokens = True
    apply_mask_config(miner_config, config.masks)
    return TemplateMiner(config=miner_config)


@dataclass(frozen=True)
class _TemplateMergeContext:
    """Inputs for merging a mined message into a session template."""

    cluster_id: str
    template_text: str
    record: LogRecord
    message: str
    existing: Template | None
    max_examples: int


def _new_template(context: _TemplateMergeContext) -> Template:
    """Build a template for the first occurrence in a cluster."""
    return Template(
        id=context.cluster_id,
        template=context.template_text,
        occurrence_count=1,
        first_seen=context.record.timestamp,
        last_seen=context.record.timestamp,
        examples=(context.message,),
    )


def _merged_template(context: _TemplateMergeContext, existing: Template) -> Template:
    """Merge a mined message into an existing template."""
    return Template(
        id=context.cluster_id,
        template=context.template_text,
        occurrence_count=existing.occurrence_count + 1,
        first_seen=_min_timestamp(existing.first_seen, context.record.timestamp),
        last_seen=_max_timestamp(existing.last_seen, context.record.timestamp),
        examples=_merge_examples(
            existing.examples,
            context.message,
            max_examples=context.max_examples,
        ),
    )


def _build_template(context: _TemplateMergeContext) -> Template:
    if context.existing is None:
        return _new_template(context)
    return _merged_template(context, context.existing)


def _store_delta_template(
    *,
    cluster_id: str,
    template_text: str,
    record: LogRecord,
    message: str,
) -> Template:
    """Build a single-occurrence template row for incremental store upserts."""
    return Template(
        id=cluster_id,
        template=template_text,
        occurrence_count=1,
        first_seen=record.timestamp,
        last_seen=record.timestamp,
        examples=(message,),
    )


@dataclass
class TemplateExtractor:
    """Mine parameterized templates from normalized log records."""

    config: OntologConfig = field(default_factory=default_config)
    store: SqliteTemplateStore | None = None
    max_examples: int = 5
    _templates: dict[str, Template] = field(default_factory=dict, init=False, repr=False)
    _miner: TemplateMiner = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._miner = _create_miner(self.config)

    def ingest(self, record: LogRecord) -> Template | None:
        """Mine or update a template for one log record."""
        message = _normalized_message(record)
        if message is None:
            return None

        try:
            return self._ingest_unsafe(record, message)
        except Exception as exc:
            message_text = f"template extraction failed: {exc}"
            raise TemplateError(message_text) from exc

    def _ingest_unsafe(self, record: LogRecord, message: str) -> Template:
        """Mine and persist a template without error translation."""
        mined = self._mine_message(message)
        cluster_id, existing = self._lookup_existing(mined.cluster_id, mined.template_text)
        parameters = self._extract_parameters(mined.template_text, message)
        template = _build_template(
            _TemplateMergeContext(
                cluster_id=cluster_id,
                template_text=mined.template_text,
                record=record,
                message=message,
                existing=existing,
                max_examples=self.max_examples,
            )
        )
        self._templates[cluster_id] = template
        self._persist(cluster_id, mined.template_text, record, message, parameters)
        return template

    def _mine_message(self, message: str) -> _MinedMessage:
        result: dict[str, Any] = self._miner.add_log_message(message)
        return _MinedMessage(
            template_text=result["template_mined"],
            cluster_id=_cluster_id(result["cluster_id"]),
        )

    def _lookup_existing(self, cluster_id: str, template_text: str) -> tuple[str, Template | None]:
        cluster_id = self._resolve_cluster_id(cluster_id, template_text)
        existing = self._templates.get(cluster_id)
        if existing is not None:
            return cluster_id, existing
        return cluster_id, self._find_stored_template(template_text)

    def _resolve_cluster_id(self, cluster_id: str, template_text: str) -> str:
        if self.store is None:
            return cluster_id
        stored_id = self.store.resolve_template_id(template_text)
        if stored_id is None:
            return cluster_id
        return stored_id

    def _find_stored_template(self, template_text: str) -> Template | None:
        if self.store is None:
            return None
        for stored in self.store.list_templates():
            if stored.template == template_text:
                return stored
        return None

    def _extract_parameters(
        self,
        template_text: str,
        message: str,
    ) -> tuple[TemplateParameter, ...]:
        extracted = self._miner.extract_parameters(template_text, message)
        return tuple(
            TemplateParameter(name=param.mask_name, value=param.value) for param in extracted
        )

    def _persist(
        self,
        cluster_id: str,
        template_text: str,
        record: LogRecord,
        message: str,
        parameters: tuple[TemplateParameter, ...],
    ) -> None:
        if self.store is None:
            return
        self.store.upsert_template(
            _store_delta_template(
                cluster_id=cluster_id,
                template_text=template_text,
                record=record,
                message=message,
            )
        )
        self.store.insert_occurrence(
            TemplateOccurrence(
                template_id=cluster_id,
                timestamp=record.timestamp,
                message=message,
                parameters=parameters,
                process=record.process,
            )
        )

    def templates(self) -> list[Template]:
        """Return all templates seen in this extractor session."""
        return sorted(
            self._templates.values(),
            key=lambda item: (-item.occurrence_count, item.template),
        )


@dataclass(frozen=True)
class ExtractOptions:
    """Options controlling template extraction."""

    format: LogFormat = LogFormat.AUTO
    preprocessors: tuple[str, ...] = ()
    skip_errors: bool = False
    limit: int | None = None


def extract_templates(
    source: Path | str,
    options: ExtractOptions,
    *,
    config: OntologConfig | None = None,
    store: SqliteTemplateStore | None = None,
) -> list[Template]:
    """Ingest a log source and return mined templates."""
    ingest_options = IngestOptions(
        format=options.format,
        preprocessors=options.preprocessors,
        skip_errors=options.skip_errors,
        limit=options.limit,
    )
    extractor = TemplateExtractor(config=config or default_config(), store=store)
    for record in ingest_path(source, ingest_options):
        extractor.ingest(record)
    if store is not None:
        store.flush()
    return extractor.templates()
