import hashlib
from pathlib import Path

import pytest
from shiftpoint_replay.download import ChecksumError, verify


def test_verify_accepts_matching_hash(tmp_path: Path) -> None:
    path = tmp_path / "f"
    path.write_bytes(b"data")

    verify(path, hashlib.sha256(b"data").hexdigest())


def test_verify_rejects_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "f"
    path.write_bytes(b"data")

    with pytest.raises(ChecksumError):
        verify(path, "0" * 64)
