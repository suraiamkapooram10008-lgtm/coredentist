#!/bin/bash
# Database Backup Script for CoreDent API
# Run this script daily via cron job

set -e

# Configuration
BACKUP_DIR="/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_NAME="${POSTGRES_DB:-coredent_db}"
DB_USER="${POSTGRES_USER:-coredent}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
RETENTION_DAYS=30

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Backup filename
BACKUP_FILE="$BACKUP_DIR/coredent_backup_$TIMESTAMP.sql.gz"

echo "Starting database backup..."
echo "Database: $DB_NAME"
echo "Timestamp: $TIMESTAMP"

# Perform backup
PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
  -h "$DB_HOST" \
  -p "$DB_PORT" \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  --format=custom \
  --compress=9 \
  --file="$BACKUP_FILE"

# Check if backup was successful
if [ $? -eq 0 ]; then
  echo "Backup completed successfully: $BACKUP_FILE"
  
  # Get backup size
  BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
  echo "Backup size: $BACKUP_SIZE"
  
  # Remove old backups (older than RETENTION_DAYS)
  echo "Cleaning up old backups (older than $RETENTION_DAYS days)..."
  find "$BACKUP_DIR" -name "coredent_backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete
  
  echo "Backup process completed successfully"
  exit 0
else
  echo "ERROR: Backup failed!"
  exit 1
fi
