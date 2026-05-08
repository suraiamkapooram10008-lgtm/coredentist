#!/bin/bash
# Database Backup Cron Job Setup
# Sets up automated daily backups

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup.py"
LOG_FILE="$SCRIPT_DIR/backup.log"

# Create cron job for daily backups at 2 AM
CRON_JOB="0 2 * * * cd $SCRIPT_DIR && python3 $BACKUP_SCRIPT >> $LOG_FILE 2>&1"

# Check if cron job already exists
if crontab -l | grep -q "$BACKUP_SCRIPT"; then
    echo "✅ Backup cron job already exists"
else
    # Add cron job
    (crontab -l ; echo "$CRON_JOB") | crontab -
    echo "✅ Backup cron job added: Daily at 2 AM"
fi

# Test the backup script
echo "🧪 Testing backup script..."
cd "$SCRIPT_DIR"
python3 "$BACKUP_SCRIPT" --dry-run 2>/dev/null && echo "✅ Backup script is working" || echo "⚠️  Backup script test failed"

echo "📋 Current cron jobs:"
crontab -l | grep backup || echo "No backup cron jobs found"

echo ""
echo "📖 Backup Instructions:"
echo "  • Daily backups run automatically at 2 AM"
echo "  • Backups stored in ./backups/ directory"
echo "  • Old backups (>30 days) are automatically cleaned up"
echo "  • View logs: tail -f $LOG_FILE"
echo "  • Manual backup: python3 $BACKUP_SCRIPT"
echo "  • Restore: python3 restore.py <backup_file>"