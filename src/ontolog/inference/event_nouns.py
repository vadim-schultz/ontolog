"""Extract domain nouns from event slug labels."""

from __future__ import annotations

_LIFECYCLE_SUFFIXES: tuple[str, ...] = (
    "completed",
    "created",
    "deleted",
    "established",
    "received",
    "running",
    "sent",
    "updated",
    "validated",
)


def event_noun_from_slug(slug: str) -> str | None:
    """Return the noun prefix from an event slug such as ``ordercreated``."""
    lowered = slug.lower()
    for suffix in _LIFECYCLE_SUFFIXES:
        if lowered.endswith(suffix) and len(lowered) > len(suffix):
            return lowered[: -len(suffix)]
    return None
