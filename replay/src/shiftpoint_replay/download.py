"""Download the pinned TwinRouterBench question bank into ``data/``.

Usage: ``uv run python -m shiftpoint_replay.download [--dest DIR] [--force]``
"""

from __future__ import annotations

import argparse
import hashlib
import urllib.request
from pathlib import Path

REPO = "Amorph/TwinRouterBench"
REVISION = "c2907f006455d9d3b4bf69472a527536c7baa195"
FILENAME = "question_bank.jsonl"
SHA256 = "7e2870b5e2e5c801f6444c05a4311c9c9010e965016f6938f0bb5abc226252d0"
DEFAULT_DEST = Path("data/twinrouterbench")


class ChecksumError(RuntimeError):
    """Downloaded file does not match the pinned checksum."""


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(path: Path, expected: str = SHA256) -> None:
    actual = sha256_of(path)
    if actual != expected:
        raise ChecksumError(f"{path}: sha256 {actual} != expected {expected}")


def download(dest: Path = DEFAULT_DEST, *, force: bool = False) -> Path:
    """Fetch the question bank at the pinned revision; return its local path."""
    target = dest / FILENAME
    if target.exists() and not force:
        verify(target)
        return target
    dest.mkdir(parents=True, exist_ok=True)
    url = f"https://huggingface.co/datasets/{REPO}/resolve/{REVISION}/{FILENAME}"
    partial = target.with_suffix(".part")
    with urllib.request.urlopen(url, timeout=120) as response, partial.open("wb") as fh:
        while chunk := response.read(1 << 20):
            fh.write(chunk)
    try:
        verify(partial)
    except ChecksumError:
        partial.unlink()
        raise
    partial.replace(target)
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    parser.add_argument("--force", action="store_true", help="re-download even if present")
    args = parser.parse_args()
    print(download(args.dest, force=args.force))


if __name__ == "__main__":
    main()
