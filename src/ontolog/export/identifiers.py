"""Validate and sanitize Python field identifiers for export."""

from __future__ import annotations

import keyword


def is_valid_field_name(name: str) -> bool:
    """Return whether ``name`` is usable as a Python field name."""
    return to_python_identifier(name) is not None


def to_python_identifier(name: str) -> str | None:
    """Return a Python identifier for ``name``, or ``None`` when not possible."""
    if not name:
        return None
    cleaned = name.strip()
    if not cleaned.isidentifier():
        return None
    if keyword.iskeyword(cleaned):
        return f"{cleaned}_"
    return cleaned
