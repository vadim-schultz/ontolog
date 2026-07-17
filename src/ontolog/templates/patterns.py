"""Shared regex patterns for masking and type inference."""

from __future__ import annotations

from ontolog.config import MaskKind

_BOUNDARY_PREFIX = r"((?<=[^A-Za-z0-9])|^)"
_BOUNDARY_SUFFIX = r"((?=[^A-Za-z0-9])|$)"

MASK_PATTERNS: dict[MaskKind, str] = {
    MaskKind.IP: (
        rf"{_BOUNDARY_PREFIX}(\d{{1,3}}\.\d{{1,3}}\.\d{{1,3}}\.\d{{1,3}}){_BOUNDARY_SUFFIX}"
    ),
    MaskKind.UUID: (
        rf"{_BOUNDARY_PREFIX}"
        r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
        rf"{_BOUNDARY_SUFFIX}"
    ),
    MaskKind.MAC: (
        rf"{_BOUNDARY_PREFIX}"
        r"([0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}|"
        r"[0-9a-fA-F]{2}(-[0-9a-fA-F]{2}){5})"
        rf"{_BOUNDARY_SUFFIX}"
    ),
    MaskKind.HEX: rf"{_BOUNDARY_PREFIX}(0x[0-9a-fA-F]+){_BOUNDARY_SUFFIX}",
    MaskKind.EMAIL: (
        rf"{_BOUNDARY_PREFIX}([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{{2,}}){_BOUNDARY_SUFFIX}"
    ),
    MaskKind.NUMBER: rf"{_BOUNDARY_PREFIX}([-+]?\d+(?:\.\d+)?){_BOUNDARY_SUFFIX}",
    MaskKind.TIMESTAMP: (
        rf"{_BOUNDARY_PREFIX}"
        r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)"
        rf"{_BOUNDARY_SUFFIX}"
    ),
}

TYPE_PATTERNS: dict[str, str] = {
    "ipv4": MASK_PATTERNS[MaskKind.IP],
    "ipv6": (
        rf"{_BOUNDARY_PREFIX}"
        r"(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|"
        r"([0-9a-fA-F]{1,4}:){1,7}:|"
        r"([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|"
        r"([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|"
        r"([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|"
        r"([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|"
        r"([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|"
        r"[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|"
        r":((:[0-9a-fA-F]{1,4}){1,7}|:))"
        rf"{_BOUNDARY_SUFFIX}"
    ),
    "uuid": MASK_PATTERNS[MaskKind.UUID],
    "mac": MASK_PATTERNS[MaskKind.MAC],
    "hex": MASK_PATTERNS[MaskKind.HEX],
    "email": MASK_PATTERNS[MaskKind.EMAIL],
    "int": r"^-?\d+$",
    "float": r"^-?\d+\.\d+$",
    "bool": r"^(?i:true|false)$",
    "url": r"^https?://[^\s]+$",
    "path": r"^(/[^\s]+|[A-Za-z]:\\[^\s]+)$",
    "timestamp": MASK_PATTERNS[MaskKind.TIMESTAMP],
    "number": MASK_PATTERNS[MaskKind.NUMBER],
}

STRONG_TYPE_SCORES: dict[str, float] = {
    "ipv4": 0.95,
    "ipv6": 0.95,
    "uuid": 0.95,
    "mac": 0.95,
    "hex": 0.95,
    "email": 0.9,
    "timestamp": 0.9,
}

WEAK_TYPE_SCORE = 0.75
