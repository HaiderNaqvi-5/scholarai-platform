#!/bin/sh
set -eu

if [ -n "${DB_PASSWORD:-}" ] && [ -z "${PGPASSWORD:-}" ]; then
  export PGPASSWORD="${DB_PASSWORD}"
fi

if [ "${WAIT_FOR_DB:-0}" = "1" ]; then
  db_host="${POSTGRES_HOST:-postgres}"
  db_port="${POSTGRES_PORT:-5432}"
  db_user="${POSTGRES_USER:-scholarai}"
  db_name="${POSTGRES_DB:-scholarai}"

  echo "Waiting for PostgreSQL at ${db_host}:${db_port}"
  until pg_isready -h "${db_host}" -p "${db_port}" -U "${db_user}" -d "${db_name}" >/dev/null 2>&1; do
    sleep 2
  done
fi

if [ "${RUN_MIGRATIONS_ON_STARTUP:-0}" = "1" ]; then
  echo "Running Alembic migrations"
  python -m alembic upgrade head
fi

exec "$@"
