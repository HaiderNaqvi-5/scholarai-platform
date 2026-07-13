from __future__ import annotations

import os
import time

from app.services.privacy.export_service import EXPORT_TTL, cleanup_expired_exports


def test_cleanup_expired_exports_removes_aged_bundle_keeps_fresh(tmp_path):
    aged = tmp_path / "export-aged.zip"
    fresh = tmp_path / "export-fresh.zip"
    aged.write_bytes(b"aged")
    fresh.write_bytes(b"fresh")

    old_time = time.time() - (EXPORT_TTL.total_seconds() + 3600)
    os.utime(aged, (old_time, old_time))

    removed = cleanup_expired_exports(root=tmp_path)

    assert removed == 1
    assert not aged.exists()
    assert fresh.exists()


def test_cleanup_expired_exports_ignores_unrelated_files(tmp_path):
    unrelated = tmp_path / "not-a-bundle.txt"
    unrelated.write_text("keep me")
    old_time = time.time() - (EXPORT_TTL.total_seconds() + 3600)
    os.utime(unrelated, (old_time, old_time))

    removed = cleanup_expired_exports(root=tmp_path)

    assert removed == 0
    assert unrelated.exists()


def test_cleanup_expired_exports_missing_dir_is_noop(tmp_path):
    missing = tmp_path / "does-not-exist"

    removed = cleanup_expired_exports(root=missing)

    assert removed == 0
