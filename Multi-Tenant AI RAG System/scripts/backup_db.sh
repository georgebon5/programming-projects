#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# PostgreSQL Backup Script for Multi-Tenant RAG System
#
# Usage:
#   ./scripts/backup_db.sh                 # backup to ./backups/
#   BACKUP_DIR=/mnt/s3 ./scripts/backup_db.sh  # custom backup dir
#
# Environment variables (or .env):
#   POSTGRES_HOST     (default: localhost)
#   POSTGRES_PORT     (default: 5432)
#   POSTGRES_USER     (default: postgres)
#   POSTGRES_PASSWORD (required)
#   POSTGRES_DB       (default: multi_tenant_rag)
#   BACKUP_DIR        (default: ./backups)
#   BACKUP_RETENTION_DAYS (default: 30)
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# Load .env if present
if [[ -f .env ]]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' .env | xargs)
fi

POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-multi_tenant_rag}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION="${BACKUP_RETENTION_DAYS:-30}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="${POSTGRES_DB}_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup of ${POSTGRES_DB}..."

export PGPASSWORD="${POSTGRES_PASSWORD}"

pg_dump \
  -h "$POSTGRES_HOST" \
  -p "$POSTGRES_PORT" \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  --format=custom \
  --compress=9 \
  --no-owner \
  --no-privileges \
  -f "${BACKUP_DIR}/${POSTGRES_DB}_${TIMESTAMP}.dump"

echo "[$(date)] Backup saved: ${BACKUP_DIR}/${POSTGRES_DB}_${TIMESTAMP}.dump"

# ── Prune old backups ────────────────────────────────────────────────────────
DELETED=$(find "$BACKUP_DIR" -name "${POSTGRES_DB}_*.dump" -mtime +"$RETENTION" -delete -print | wc -l)
if [[ "$DELETED" -gt 0 ]]; then
  echo "[$(date)] Pruned $DELETED backup(s) older than ${RETENTION} days."
fi

echo "[$(date)] Backup complete."
