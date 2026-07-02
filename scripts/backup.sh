#!/bin/bash
# Personal Analytics Database Backup Script
# Can be run manually or scheduled via cron on the host.

# Set directories relative to the script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$SCRIPT_DIR/../backups"

# Ensure backups directory exists
mkdir -p "$BACKUP_DIR"

# File naming
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql"

echo "Executing pg_dump inside personal_analytics_db container..."

# Execute dump
docker exec -t personal_analytics_db pg_dump -U postgres personal_analytics > "$BACKUP_FILE"

# Check status
if [ ${PIPESTATUS[0]} -eq 0 ] && [ -s "$BACKUP_FILE" ]; then
    echo "SUCCESS: Database backup written to $BACKUP_FILE"
    # Keep only the last 30 days of backups to save disk space
    find "$BACKUP_DIR" -name "backup_*.sql" -type f -mtime +30 -delete
    echo "Older backups (30+ days) pruned."
    exit 0
else
    echo "ERROR: Database backup failed!"
    # Remove empty backup file if created
    [ -f "$BACKUP_FILE" ] && rm "$BACKUP_FILE"
    exit 1
fi
