"""Export format identifiers."""

from __future__ import annotations

from enum import StrEnum


class ExportFormat(StrEnum):
    """Supported domain model export formats."""

    PYDANTIC = "pydantic"
    JSON_SCHEMA = "json-schema"
    MERMAID = "mermaid"
    MARKDOWN = "markdown"
    GRAPHML = "graphml"
    NEO4J_CSV = "neo4j-csv"
