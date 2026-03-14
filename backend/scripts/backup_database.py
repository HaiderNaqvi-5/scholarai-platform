from __future__ import annotations

import argparse
import gzip
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def get_env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


def build_backup_path(backup_dir: Path, database_name: str, now: datetime | None = None) -> Path:
    timestamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%d-%H%M%SZ")
    return backup_dir / f"{database_name}-{timestamp}.sql.gz"


def prune_old_backups(backup_dir: Path, retention_days: int, now: datetime | None = None) -> None:
    cutoff = (now or datetime.now(timezone.utc)).timestamp() - (retention_days * 86400)

    for backup_file in backup_dir.glob("*.sql.gz"):
        if backup_file.stat().st_mtime < cutoff:
            backup_file.unlink()


def run_backup(
    *,
    host: str,
    port: int,
    database_name: str,
    user: str,
    password: str,
    backup_dir: Path,
) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = build_backup_path(backup_dir, database_name)

    env = os.environ.copy()
    env["PGPASSWORD"] = password
    command = [
        "pg_dump",
        "-h",
        host,
        "-p",
        str(port),
        "-U",
        user,
        "-d",
        database_name,
        "--no-owner",
        "--no-privileges",
    ]

    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env) as process:
        assert process.stdout is not None
        with gzip.open(backup_path, "wb") as compressed_backup:
            shutil.copyfileobj(process.stdout, compressed_backup)

        stderr_output = b""
        if process.stderr is not None:
            stderr_output = process.stderr.read()

        return_code = process.wait()

    if return_code != 0:
        backup_path.unlink(missing_ok=True)
        error_text = stderr_output.decode("utf-8", errors="ignore").strip()
        raise RuntimeError(f"pg_dump failed with exit code {return_code}: {error_text}")

    return backup_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create gzip-compressed PostgreSQL backups.")
    parser.add_argument("--loop", action="store_true", help="Run continuously using BACKUP_INTERVAL_SECONDS.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    host = os.getenv("POSTGRES_HOST", "postgres")
    port = get_env_int("POSTGRES_PORT", 5432)
    database_name = os.getenv("POSTGRES_DB", "scholarai")
    user = os.getenv("POSTGRES_USER", "scholarai")
    password = os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD", "")
    backup_dir = Path(os.getenv("BACKUP_DIR", "/backups"))
    interval_seconds = get_env_int("BACKUP_INTERVAL_SECONDS", 86400)
    retention_days = get_env_int("BACKUP_RETENTION_DAYS", 7)

    if not password:
        raise RuntimeError("DB_PASSWORD or POSTGRES_PASSWORD must be set for database backups.")

    while True:
        backup_path = run_backup(
            host=host,
            port=port,
            database_name=database_name,
            user=user,
            password=password,
            backup_dir=backup_dir,
        )
        prune_old_backups(backup_dir, retention_days)
        print(f"Created backup: {backup_path}")

        if not args.loop:
            return 0

        time.sleep(interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
