"""Tests for scripts/fetch_corpora.py."""

from __future__ import annotations

import importlib.util
import tarfile
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "fetch_corpora.py"
_SPEC = importlib.util.spec_from_file_location("fetch_corpora", _MODULE_PATH)
assert _SPEC and _SPEC.loader
fetch_corpora = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(fetch_corpora)


def test_parse_tier_cli_arg() -> None:
    assert fetch_corpora.parse_tier("integration") is fetch_corpora.Tier.INTEGRATION
    assert fetch_corpora.parse_tier("benchmark") is fetch_corpora.Tier.BENCHMARK


def test_checksum_verification_passes(tmp_path: Path) -> None:
    payload = tmp_path / "sample.tar.gz"
    payload.write_bytes(b"test-data")
    digest = __import__("hashlib").sha256(payload.read_bytes()).hexdigest()
    fetch_corpora.verify_checksum(payload, digest)


def test_checksum_verification_fails(tmp_path: Path) -> None:
    payload = tmp_path / "sample.tar.gz"
    payload.write_bytes(b"test-data")
    with pytest.raises(ValueError, match="checksum mismatch"):
        fetch_corpora.verify_checksum(payload, "deadbeef")


def test_extract_tar_gz(tmp_path: Path) -> None:
    archive_path = tmp_path / "sample.tar.gz"
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    source = tmp_path / "hello.txt"
    source.write_text("hello", encoding="utf-8")

    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(source, arcname="hello.txt")

    fetch_corpora.extract_archive(archive_path, output_dir)
    assert (output_dir / "hello.txt").read_text(encoding="utf-8") == "hello"
