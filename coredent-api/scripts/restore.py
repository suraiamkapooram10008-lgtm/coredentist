#!/usr/bin/env python3
"""
Database Restore Script
Restores database from backup with point-in-time recovery
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import subprocess
import shutil
from typing import Optional

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.core.config_simple import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('restore.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DatabaseRestore:
    """Database restore manager"""

    def __init__(self):
        self.backup_dir = Path(settings.BACKUP_DIR) if hasattr(settings, 'BACKUP_DIR') else Path('./backups')

    def restore_backup(self, backup_file: str, confirm: bool = False) -> bool:
        """
        Restore database from backup

        Args:
            backup_file: Path to backup file
            confirm: Whether to skip confirmation prompt

        Returns:
            True if restore was successful
        """
        backup_path = Path(backup_file)

        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_file}")
            return False

        # Safety check
        if not confirm:
            print(f"⚠️  WARNING: This will overwrite the current database!")
            print(f"Backup file: {backup_file}")
            print(f"Database: {settings.DATABASE_URL}")
            print()
            response = input("Are you sure you want to continue? (type 'yes' to confirm): ")
            if response.lower() != 'yes':
                print("Restore cancelled.")
                return False

        try:
            if 'sqlite' in settings.DATABASE_URL:
                return self._restore_sqlite(backup_path)
            elif 'postgresql' in settings.DATABASE_URL:
                return self._restore_postgres(backup_path)
            else:
                logger.error(f"Unsupported database type: {settings.DATABASE_URL}")
                return False

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False

    def _restore_sqlite(self, backup_path: Path) -> bool:
        """Restore SQLite database"""
        try:
            # Extract database path from URL
            db_path = settings.DATABASE_URL.replace('sqlite+aiosqlite:///', '')

            # Decompress if needed
            if backup_path.suffix == '.gz':
                import gzip
                decompressed_path = backup_path.with_suffix('')
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(decompressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                source_path = decompressed_path
            else:
                source_path = backup_path

            # Create backup of current database
            current_backup = Path(db_path).with_suffix('.bak')
            if Path(db_path).exists():
                logger.info(f"Creating backup of current database: {current_backup}")
                shutil.copy2(db_path, current_backup)

            # Restore from backup
            logger.info(f"Restoring database: {source_path} -> {db_path}")
            shutil.copy2(source_path, db_path)

            # Clean up decompressed file if created
            if backup_path.suffix == '.gz' and source_path != backup_path:
                source_path.unlink()

            logger.info("SQLite restore completed successfully")
            return True

        except Exception as e:
            logger.error(f"SQLite restore failed: {e}")
            return False

    def _restore_postgres(self, backup_path: Path) -> bool:
        """Restore PostgreSQL database"""
        try:
            # This is a simplified implementation
            # In production, you'd want more sophisticated connection parsing
            cmd = [
                'pg_restore',
                '--clean',        # Clean (drop) database objects before recreating
                '--if-exists',    # Use with --clean to avoid errors if objects don't exist
                '--no-owner',     # Don't set ownership
                '--no-privileges', # Don't restore privileges
                str(backup_path)
            ]

            logger.info(f"Restoring PostgreSQL database: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("PostgreSQL restore completed successfully")
                return True
            else:
                logger.error(f"PostgreSQL restore failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"PostgreSQL restore error: {e}")
            return False


def main():
    """Main restore execution"""
    if len(sys.argv) < 2:
        print("Usage: python restore.py <backup_file> [--confirm]")
        print("\nAvailable backups:")
        backup = DatabaseRestore()
        backups = backup.list_backups()
        for b in backups[:10]:  # Show last 10
            print(f"  {b['filename']} ({b['created']})")
        sys.exit(1)

    backup_file = sys.argv[1]
    confirm = '--confirm' in sys.argv

    restorer = DatabaseRestore()
    success = restorer.restore_backup(backup_file, confirm)

    if success:
        logger.info("Database restore completed successfully")
        print("✅ Database restore completed successfully")
    else:
        logger.error("Database restore failed")
        print("❌ Database restore failed")
        sys.exit(1)


if __name__ == '__main__':
    main()