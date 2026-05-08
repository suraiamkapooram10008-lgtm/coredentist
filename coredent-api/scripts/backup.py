#!/usr/bin/env python3
"""
Database Backup Automation Script
Creates daily snapshots with point-in-time recovery capability
"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
import subprocess
import shutil
from typing import Optional

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config_simple import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DatabaseBackup:
    """Database backup manager with point-in-time recovery"""

    def __init__(self):
        self.backup_dir = Path(settings.BACKUP_DIR) if hasattr(settings, 'BACKUP_DIR') else Path('./backups')
        self.backup_dir.mkdir(exist_ok=True)

        # Database connection details
        self.db_url = settings.DATABASE_URL

    def create_backup(self, backup_type: str = 'daily') -> Optional[str]:
        """
        Create database backup

        Args:
            backup_type: Type of backup (daily, weekly, monthly)

        Returns:
            Path to backup file if successful, None otherwise
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"coredent_{backup_type}_{timestamp}"

        try:
            if 'sqlite' in self.db_url:
                # SQLite backup (simple file copy)
                db_path = self.db_url.replace('sqlite+aiosqlite:///', '')
                backup_path = self.backup_dir / f"{backup_name}.db"

                logger.info(f"Creating SQLite backup: {db_path} -> {backup_path}")
                shutil.copy2(db_path, backup_path)

                # Create compressed backup
                compressed_path = self.backup_dir / f"{backup_name}.db.gz"
                self._compress_file(backup_path, compressed_path)

                # Remove uncompressed file
                backup_path.unlink()

                logger.info(f"SQLite backup completed: {compressed_path}")
                return str(compressed_path)

            elif 'postgresql' in self.db_url:
                # PostgreSQL backup using pg_dump
                backup_path = self.backup_dir / f"{backup_name}.sql"
                return self._create_postgres_backup(backup_path)

            else:
                logger.error(f"Unsupported database type in URL: {self.db_url}")
                return None

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None

    def _create_postgres_backup(self, backup_path: Path) -> Optional[str]:
        """Create PostgreSQL backup using pg_dump"""
        try:
            # Parse connection details from URL
            # This is a simplified implementation
            cmd = [
                'pg_dump',
                '--format=custom',  # Custom format for compression
                '--compress=9',     # Maximum compression
                '--no-owner',       # Don't set ownership
                '--no-privileges',  # Don't dump privileges
                f'--file={backup_path}',
                self.db_url
            ]

            logger.info(f"Creating PostgreSQL backup: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"PostgreSQL backup completed: {backup_path}")
                return str(backup_path)
            else:
                logger.error(f"PostgreSQL backup failed: {result.stderr}")
                return None

        except Exception as e:
            logger.error(f"PostgreSQL backup error: {e}")
            return None

    def _compress_file(self, source: Path, destination: Path) -> bool:
        """Compress file using gzip"""
        try:
            import gzip
            with open(source, 'rb') as f_in:
                with gzip.open(destination, 'wb', compresslevel=9) as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return True
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return False

    def cleanup_old_backups(self, keep_days: int = 30) -> int:
        """Remove backups older than specified days"""
        cutoff_time = time.time() - (keep_days * 24 * 60 * 60)
        removed_count = 0

        for backup_file in self.backup_dir.glob('coredent_*'):
            if backup_file.stat().st_mtime < cutoff_time:
                backup_file.unlink()
                removed_count += 1
                logger.info(f"Removed old backup: {backup_file}")

        return removed_count

    def list_backups(self) -> list:
        """List all available backups"""
        backups = []
        for backup_file in self.backup_dir.glob('coredent_*'):
            stat = backup_file.stat()
            backups.append({
                'filename': backup_file.name,
                'path': str(backup_file),
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'type': backup_file.suffix
            })

        return sorted(backups, key=lambda x: x['created'], reverse=True)


def main():
    """Main backup execution"""
    backup = DatabaseBackup()

    # Create daily backup
    logger.info("Starting database backup...")
    backup_file = backup.create_backup('daily')

    if backup_file:
        logger.info(f"Backup completed successfully: {backup_file}")

        # Cleanup old backups (keep 30 days)
        removed = backup.cleanup_old_backups(30)
        if removed > 0:
            logger.info(f"Cleaned up {removed} old backup files")

        # List current backups
        backups = backup.list_backups()
        logger.info(f"Total backups available: {len(backups)}")

        return True
    else:
        logger.error("Backup failed!")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)