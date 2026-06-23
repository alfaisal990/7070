#!/bin/bash
# Phoenix AI Disaster Recovery Backup/Restore Script
# Usage:
#   ./backup_restore.sh backup
#   ./backup_restore.sh restore [backup_file_path]

DB_PATH="ai_project/memory/memory_db.json"
BACKUP_DIR="ai_project/memory/backups"

backup() {
    echo "Starting memory database backup..."
    if [ ! -f "$DB_PATH" ]; then
        echo "ERROR: Database file not found at $DB_PATH. Nothing to backup."
        exit 1
    fi

    mkdir -p "$BACKUP_DIR"
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="$BACKUP_DIR/memory_db_$TIMESTAMP.json"
    TEMP_FILE="$BACKUP_FILE.tmp"

    # Copy database file
    cp "$DB_PATH" "$TEMP_FILE"

    # Verify integrity using Python one-liner
    python3 -c "
import json
with open('$TEMP_FILE', 'r') as f:
    data = json.load(f)
    assert 'memories' in data and 'kg_graph' in data, 'Missing core fields'
" 2>/dev/null

    if [ $? -eq 0 ]; then
        mv "$TEMP_FILE" "$BACKUP_FILE"
        echo "SUCCESS: Backup created at $BACKUP_FILE"
        
        # Rotate backups (keep latest 5)
        cd "$BACKUP_DIR" || exit 1
        ls -t memory_db_*.json 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null
        cd - >/dev/null || exit 1
    else
        rm -f "$TEMP_FILE"
        echo "ERROR: Backup integrity validation failed."
        exit 1
    fi
}

restore() {
    local target_backup="$1"
    
    # If no file is specified, look for the latest backup
    if [ -z "$target_backup" ]; then
        echo "No backup file specified. Locating the latest backup..."
        target_backup=$(ls -t "$BACKUP_DIR"/memory_db_*.json 2>/dev/null | head -n 1)
        if [ -z "$target_backup" ]; then
            echo "ERROR: No backups found in $BACKUP_DIR."
            exit 1
        fi
    fi

    if [ ! -f "$target_backup" ]; then
        echo "ERROR: Backup file not found at $target_backup"
        exit 1
    fi

    echo "Restoring database from $target_backup..."
    
    # Verify backup integrity before restoring
    python3 -c "
import json
with open('$target_backup', 'r') as f:
    data = json.load(f)
    assert 'memories' in data and 'kg_graph' in data, 'Missing core fields'
" 2>/dev/null

    if [ $? -ne 0 ]; then
        echo "ERROR: Target backup file is corrupted or invalid."
        exit 1
    fi

    # Create safety copy of current db before overwriting
    if [ -f "$DB_PATH" ]; then
        cp "$DB_PATH" "$DB_PATH.safety"
    fi

    cp "$target_backup" "$DB_PATH"
    
    if [ $? -eq 0 ]; then
        echo "SUCCESS: Database restored successfully from $target_backup"
        if [ -f "$DB_PATH.safety" ]; then
            rm -f "$DB_PATH.safety"
        fi
    else
        echo "ERROR: Restore failed. Reverting to safety copy..."
        if [ -f "$DB_PATH.safety" ]; then
            mv "$DB_PATH.safety" "$DB_PATH"
        fi
        exit 1
    fi
}

# Main routing
ACTION="$1"
shift

case "$ACTION" in
    backup)
        backup
        ;;
    restore)
        restore "$1"
        ;;
    *)
        echo "Usage: $0 {backup|restore} [backup_file_path]"
        exit 1
        ;;
esac
