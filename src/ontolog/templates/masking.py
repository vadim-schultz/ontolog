"""Bridge Ontolog mask configuration to Drain3 masking instructions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from drain3.masking import MaskingInstruction

from ontolog.config import MaskConfig, MaskKind
from ontolog.templates.patterns import MASK_PATTERNS

if TYPE_CHECKING:
    from drain3.template_miner_config import TemplateMinerConfig


def build_masking_instructions(masks: MaskConfig) -> list[dict[str, str]]:
    """Return Drain3-compatible masking instruction dicts."""
    instructions: list[dict[str, str]] = []
    for kind in MaskKind:
        if kind not in masks.enabled:
            continue
        instructions.append(
            {
                "regex_pattern": MASK_PATTERNS[kind],
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
