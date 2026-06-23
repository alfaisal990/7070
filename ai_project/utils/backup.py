import os
import json
import shutil
import glob
from datetime import datetime

class PhoenixBackupManager:
    """
    Manages atomic backups, validation, and rotation of the memory database.
    """
    def __init__(self, db_path: str = "ai_project/memory/memory_db.json", backup_dir: str = "ai_project/memory/backups", max_backups: int = 5):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.max_backups = max_backups

    def create_backup(self) -> str:
        """
        Creates an atomic backup of the database, verifies its integrity,
        and rotates older backups. Returns the path of the created backup.
        """
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database file not found at {self.db_path}. Nothing to backup.")

        os.makedirs(self.backup_dir, exist_ok=True)
        
        # 1. Generate timestamped file name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_filename = f"memory_db_{timestamp}.json"
        dest_path = os.path.join(self.backup_dir, dest_filename)
        temp_dest_path = dest_path + ".tmp"
        
        try:
            # 2. Atomic copy
            shutil.copy2(self.db_path, temp_dest_path)
            
            # 3. Verify integrity
            with open(temp_dest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Verify basic structure
                if "memories" not in data or "kg_graph" not in data:
                    raise ValueError("Integrity check failed: missing required structure fields.")
            
            # Rename temp to target atomically
            os.replace(temp_dest_path, dest_path)
            
            # 4. Rotate old backups
            self.rotate_backups()
            
            return dest_path
            
        except Exception as e:
            if os.path.exists(temp_dest_path):
                try:
                    os.remove(temp_dest_path)
                except OSError:
                    pass
            raise IOError(f"Backup creation failed: {str(e)}")

    def rotate_backups(self):
        """Keep only the most recent 'max_backups' files, deleting the rest."""
        pattern = os.path.join(self.backup_dir, "memory_db_*.json")
        backup_files = glob.glob(pattern)
        
        # Sort files by creation / modification time (oldest first)
        backup_files.sort(key=os.path.getmtime)
        
        # Delete oldest files if we exceed max_backups
        if len(backup_files) > self.max_backups:
            to_delete = backup_files[:-self.max_backups]
            for file_path in to_delete:
                try:
                    os.remove(file_path)
                except OSError:
                    pass
