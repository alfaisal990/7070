import os
import sys
import json
import argparse
import shutil

def restore_db(backup_file: str, db_file: str = "ai_project/memory/memory_db.json"):
    if not os.path.exists(backup_file):
        print(f"Error: Backup file {backup_file} does not exist.")
        sys.exit(1)
        
    print(f"Validating backup integrity for {backup_file}...")
    try:
        with open(backup_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "memories" not in data or "kg_graph" not in data:
                raise ValueError("Required database root keys are missing.")
        print("Backup integrity validation: OK.")
    except Exception as e:
        print(f"Error: Backup file is corrupt or invalid: {str(e)}")
        sys.exit(1)
        
    print(f"Restoring database to {db_file}...")
    temp_db = db_file + ".restore.tmp"
    try:
        # Ensure destination folder exists
        os.makedirs(os.path.dirname(os.path.abspath(db_file)), exist_ok=True)
        shutil.copy2(backup_file, temp_db)
        os.replace(temp_db, db_file)
        print("Database restored successfully.")
    except Exception as e:
        if os.path.exists(temp_db):
            os.remove(temp_db)
        print(f"Error restoring database: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Restore Phoenix Memory DB from a backup file.")
    parser.add_argument("--file", required=True, help="Path to the backup JSON file.")
    parser.add_argument("--dest", default="ai_project/memory/memory_db.json", help="Path to destination database file.")
    args = parser.parse_args()
    restore_db(args.file, args.dest)
