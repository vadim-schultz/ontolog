"""Shared formatting helpers for export output."""

from __future__ import annotations


def confidence_suffix(value: float) -> str:
    """Return a parenthetical confidence label for ``value``."""
    return f"(confidence={value:.2f})"
