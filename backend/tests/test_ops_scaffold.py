from datetime import datetime, timedelta, timezone
from pathlib import Path
import os

from scripts.backup_database import build_backup_path, prune_old_backups


def test_build_backup_path_uses_database_name_and_timestamp(tmp_path):
    now = datetime(2026, 3, 14, 12, 30, tzinfo=timezone.utc)

    backup_path = build_backup_path(tmp_path, "scholarai", now=now)

    assert backup_path.name == "scholarai-20260314-123000Z.sql.gz"


def test_prune_old_backups_removes_files_older_than_retention(tmp_path):
    old_file = tmp_path / "old.sql.gz"
    recent_file = tmp_path / "recent.sql.gz"
    old_file.write_bytes(b"old")
    recent_file.write_bytes(b"recent")

    now = datetime(2026, 3, 14, 12, 30, tzinfo=timezone.utc)
    old_time = (now - timedelta(days=10)).timestamp()
    recent_time = (now - timedelta(days=1)).timestamp()
    os.utime(old_file, (old_time, old_time))
    os.utime(recent_file, (recent_time, recent_time))

    prune_old_backups(tmp_path, retention_days=7, now=now)

    assert not old_file.exists()
    assert recent_file.exists()


def test_compose_includes_flower_and_postgres_backup_services():
    repo_root = Path(__file__).resolve().parents[2]
    compose_text = (repo_root / "docker-compose.yml").read_text(encoding="utf-8")

    assert "flower:" in compose_text
    assert "postgres-backup:" in compose_text
    assert "5555:5555" in compose_text


def test_backend_dockerfile_uses_entrypoint_script():
    backend_root = Path(__file__).resolve().parents[1]
    dockerfile_text = (backend_root / "Dockerfile").read_text(encoding="utf-8")

    assert 'ENTRYPOINT ["./scripts/docker-entrypoint.sh"]' in dockerfile_text


def test_backend_service_runs_migrations_on_startup():
    repo_root = Path(__file__).resolve().parents[2]
    compose_text = (repo_root / "docker-compose.yml").read_text(encoding="utf-8")

    assert 'RUN_MIGRATIONS_ON_STARTUP: "1"' in compose_text
    assert "docker-entrypoint.sh" in (repo_root / "backend" / "Dockerfile").read_text(encoding="utf-8")
