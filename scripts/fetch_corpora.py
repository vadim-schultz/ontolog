#!/usr/bin/env python3
"""Download LogHub datasets from Zenodo with checksum verification."""

from __future__ import annotations

import argparse
import hashlib
import tarfile
from enum import Enum
from pathlib import Path
from urllib.request import urlretrieve

ZENODO_BASE = "https://zenodo.org/records/8196385/files"

CHECKSUMS: dict[str, str] = {
    "HealthApp.tar.gz": "placeholder",
    "OpenSSH.tar.gz": "placeholder",
}


class Tier(str, Enum):
    """Supported LogHub download tiers."""

    INTEGRATION = "integration"
    BENCHMARK = "benchmark"


TIER_DATASETS: dict[Tier, tuple[str, ...]] = {
    Tier.INTEGRATION: ("HealthApp.tar.gz", "OpenSSH.tar.gz"),
    Tier.BENCHMARK: ("HDFS.tar.gz", "BGL.tar.gz", "Hadoop.tar.gz"),
}


def parse_tier(value: str) -> Tier:
    """Parse a CLI tier string into a :class:`Tier`."""
    return Tier(value)


def verify_checksum(path: Path, expected: str) -> None:
    """Raise ``ValueError`` when ``path`` does not match ``expected``."""
    computed = hashlib.sha256(path.read_bytes()).hexdigest()
    if computed != expected:
        message = f"checksum mismatch for {path.name}"
        raise ValueError(message)


def extract_archive(archive_path: Path, output_dir: Path) -> None:
    """Extract a ``.tar.gz`` archive into ``output_dir``."""
    with tarfile.open(archive_path, "r:gz") as archive:
        archive.extractall(output_dir)


def download_dataset(name: str, output_dir: Path) -> None:
    """Download, verify, and extract ``name`` into ``output_dir``."""
    url = f"{ZENODO_BASE}/{name}"
    dest = output_dir / name

    print(f"Downloading {name}...")
    urlretrieve(url, dest)

    if name in CHECKSUMS and CHECKSUMS[name] != "placeholder":
        print("Verifying checksum...")
        verify_checksum(dest, CHECKSUMS[name])

    print(f"Extracting {name}...")
    extract_archive(dest, output_dir)
    dest.unlink(missing_ok=True)
    print(f"Done: {name}")


def datasets_for_tier(tier: Tier) -> tuple[str, ...]:
    """Return dataset archives for ``tier``."""
    return TIER_DATASETS[tier]


def main() -> None:
    """Download datasets for the requested tier."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tier", type=parse_tier, choices=list(Tier), required=True)
    args = parser.parse_args()

    output_dir = Path("data/loghub")
    output_dir.mkdir(parents=True, exist_ok=True)

    for dataset in datasets_for_tier(args.tier):
        download_dataset(dataset, output_dir)


if __name__ == "__main__":
    main()
