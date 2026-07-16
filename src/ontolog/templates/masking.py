"""Bridge Ontolog mask configuration to Drain3 masking instructions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from drain3.masking import MaskingInstruction

from ontolog.config import MaskConfig, MaskKind

if TYPE_CHECKING:
    from drain3.template_miner_config import TemplateMinerConfig

_MASK_PATTERNS: dict[MaskKind, str] = {
    MaskKind.IP: (r"((?<=[^A-Za-z0-9])|^)(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})((?=[^A-Za-z0-9])|$)"),
    MaskKind.UUID: (
        r"((?<=[^A-Za-z0-9])|^)"
        r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
        r"((?=[^A-Za-z0-9])|$)"
    ),
    MaskKind.MAC: (
        r"((?<=[^A-Za-z0-9])|^)"
        r"([0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}|"
        r"[0-9a-fA-F]{2}(-[0-9a-fA-F]{2}){5})"
        r"((?=[^A-Za-z0-9])|$)"
    ),
    MaskKind.HEX: r"((?<=[^A-Za-z0-9])|^)(0x[0-9a-fA-F]+)((?=[^A-Za-z0-9])|$)",
    MaskKind.EMAIL: r"((?<=[^A-Za-z0-9])|^)([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})((?=[^A-Za-z0-9])|$)",
    MaskKind.NUMBER: r"((?<=[^A-Za-z0-9])|^)([-+]?\d+(?:\.\d+)?)((?=[^A-Za-z0-9])|$)",
    MaskKind.TIMESTAMP: (
        r"((?<=[^A-Za-z0-9])|^)"
        r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)"
        r"((?=[^A-Za-z0-9])|$)"
    ),
}


def build_masking_instructions(masks: MaskConfig) -> list[dict[str, str]]:
    """Return Drain3-compatible masking instruction dicts."""
    instructions: list[dict[str, str]] = []
    for kind in MaskKind:
        if kind not in masks.enabled:
            continue
        instructions.append(
            {
                "regex_pattern": _MASK_PATTERNS[kind],
                "mask_with": kind.name,
            }
        )
    return instructions


def apply_mask_config(config: TemplateMinerConfig, masks: MaskConfig) -> None:
    """Apply Ontolog mask settings to a Drain3 template miner config."""
    config.masking_instructions = [
        MaskingInstruction(item["regex_pattern"], item["mask_with"])
        for item in build_masking_instructions(masks)
    ]
