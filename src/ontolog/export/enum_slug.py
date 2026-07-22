"""Helpers for enum-typed field slugs."""

from __future__ import annotations

_ENUM_PREFIX = "enum:"


def enum_type_slug(values: set[str] | frozenset[str]) -> str:
    """Return a stable enum type slug for ``values``."""
    return f"{_ENUM_PREFIX}{','.join(sorted(values))}"


def is_enum_type_slug(type_slug: str) -> bool:
    """Return whether ``type_slug`` encodes an enum."""
    return type_slug.startswith(_ENUM_PREFIX)


def enum_values_from_slug(type_slug: str) -> tuple[str, ...]:
    """Return enum member values encoded in ``type_slug``."""
    if not is_enum_type_slug(type_slug):
        return ()
    return tuple(type_slug.removeprefix(_ENUM_PREFIX).split(","))
