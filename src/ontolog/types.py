"""Protocols and type aliases for ontolog extension points."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ontolog.config import ConfidenceThresholds
    from ontolog.evidence.graph import EvidenceGraph
    from ontolog.export.formats import ExportFormat
    from ontolog.export.options import ExportOptions
    from ontolog.models import LogRecord
    from ontolog.models.candidate import InferenceResult
    from ontolog.models.domain import ProbabilisticDomainModel
    from ontolog.models.finding import EvidenceFinding, ProviderInput

__all__ = ["EvidenceProvider", "Exporter", "InferencePass", "LogParser", "Preprocessor"]


class Preprocessor(Protocol):
    """Transform a raw log line before parsing."""

    @property
    def name(self) -> str:
        """Return the preprocessor identifier."""
        ...

    def process(self, line: str, *, line_number: int) -> str:
        """Return the transformed line."""
        ...


class LogParser(Protocol):
    """Parse one preprocessed log line into a :class:`~ontolog.models.LogRecord`."""

    @property
    def name(self) -> str:
        """Return the parser identifier."""
        ...

    def parse_line(self, line: str, *, line_number: int) -> LogRecord:
        """Parse ``line`` into a normalized log record."""
        ...


class EvidenceProvider(Protocol):
    """Analyze templates and occurrences to produce graph findings."""

    @property
    def name(self) -> str:
        """Return the provider identifier."""
        ...

    def analyze(
        self,
        graph: EvidenceGraph,
        data: ProviderInput,
    ) -> tuple[EvidenceFinding, ...]:
        """Return findings to apply to the evidence graph."""
        ...


class InferencePass(Protocol):
    """Promote graph evidence into structured candidates."""

    @property
    def name(self) -> str:
        """Return the inference pass identifier."""
        ...

    def infer(
        self,
        graph: EvidenceGraph,
        data: ProviderInput,
        *,
        thresholds: ConfidenceThresholds,
    ) -> InferenceResult:
        """Return candidates inferred from the populated graph."""
        ...


class Exporter(Protocol):
    """Export a probabilistic domain model to a derived artifact."""

    @property
    def format_name(self) -> ExportFormat:
        """Return the exporter format identifier."""
        ...

    def export(
        self,
        model: ProbabilisticDomainModel,
        *,
        options: ExportOptions,
    ) -> str:
        """Serialize ``model`` in this exporter's format."""
        ...
