#!/bin/bash
# Database Restore Script for CoreDent API
# Usage: ./restore_database.sh <backup_file>

set -e

# Check if backup file is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <backup_file>"
  echo "Example: $0 /backups/coredent_backup_20260316_120000.sql.gz"
  exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
  echo "ERROR: Backup file not found: $BACKUP_FILE"
  exit 1
fi

# Configuration
DB_NAME="${POSTGRES_DB:-coredent_db}"
DB_USER="${POSTGRES_USER:-coredent}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo "WARNING: This will restore the database from backup"
echo "Database: $DB_NAME"
echo "Backup file: $BACKUP_FILE"
echo ""
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo "Restore cancelled"
  exit 0
fi

echo "Starting database restore..."

# Drop existing connections
PGPASSWORD="$POSTGRES_PASSWORD" psql \
  -h "$DB_HOST" \
  -p "$DB_PORT" \
  -U "$DB_USER" \
  -d postgres \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();"

# Restore database
PGPASSWORD="$POSTGRES_PASSWORD" pg_restore \
  -h "$DB_HOST" \
  -p "$DB_PORT" \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  --clean \
  --if-exists \
  --verbose \
  "$BACKUP_FILE"

# Check if restore was successful
if [ $? -eq 0 ]; then
  echo "Database restored successfully from: $BACKUP_FILE"
  exit 0
else
  echo "ERROR: Database restore failed!"
  exit 1
fi
