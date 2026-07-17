"""Node id helpers for evidence providers."""

from __future__ import annotations

import re


def slugify(value: str) -> str:
    """Return a stable lowercase identifier."""
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip()).strip("_").lower()
    return cleaned or "unknown"


def entity_id(slug: str) -> str:
    """Return an entity node id."""
    return f"entity:{slugify(slug)}"


def field_id(template_id: str, param: str) -> str:
    """Return a field node id."""
    return f"field:{template_id}:{slugify(param)}"


def type_id(name: str) -> str:
    """Return a type node id."""
    return f"type:{slugify(name)}"


def event_id(slug: str) -> str:
    """Return an event node id."""
    return f"event:{slugify(slug)}"


def template_node_id(template_id: str) -> str:
    """Return a template sequence node id."""
    return f"template:{template_id}"
