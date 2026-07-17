"""Protocols and type aliases for ontolog extension points."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ontolog.evidence.graph import EvidenceGraph
    from ontolog.models import LogRecord
    from ontolog.models.finding import EvidenceFinding, ProviderInput

__all__ = ["EvidenceProvider", "LogParser", "Preprocessor"]


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
