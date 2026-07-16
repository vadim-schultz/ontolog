"""Tests for ontolog.templates.masking."""

from __future__ import annotations

from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig

from ontolog.config import MaskConfig, MaskKind, default_config
from ontolog.templates.masking import apply_mask_config, build_masking_instructions

_SAMPLE_LINE = "payload=0xdeadbeef dest=192.168.1.1"


def _mine_template(masks: MaskConfig, line: str) -> str:
    config = TemplateMinerConfig()
    apply_mask_config(config, masks)
    miner = TemplateMiner(config=config)
    miner.add_log_message(line)
    result = miner.add_log_message(line.replace("192.168.1.1", "192.168.1.2"))
    return result["template_mined"]


def test_all_masks_enabled_returns_seven_instructions() -> None:
    instructions = build_masking_instructions(default_config().masks)
    assert len(instructions) == 7


def test_subset_masks() -> None:
    masks = MaskConfig(enabled=frozenset({MaskKind.IP, MaskKind.HEX}))
    instructions = build_masking_instructions(masks)
    assert len(instructions) == 2
    mask_names = {item["mask_with"] for item in instructions}
    assert mask_names == {"IP", "HEX"}


def test_ip_only_vs_number_only_produces_different_templates() -> None:
    ip_only = _mine_template(MaskConfig(enabled=frozenset({MaskKind.IP})), _SAMPLE_LINE)
    number_only = _mine_template(
        MaskConfig(enabled=frozenset({MaskKind.NUMBER})),
        _SAMPLE_LINE,
    )
    assert ip_only != number_only


def test_disabled_hex_not_labeled_hex() -> None:
    template = _mine_template(
        MaskConfig(enabled=frozenset({MaskKind.IP})),
        _SAMPLE_LINE,
    )
    assert "<HEX>" not in template
