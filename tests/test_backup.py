import os
import json
import shutil
import pytest
from fastapi.testclient import TestClient
from ai_project.utils.backup import PhoenixBackupManager
from ai_project.api.main import app
from ai_project.api.auth import create_access_token, Roles

def test_backup_manager(tmp_path):
    # Create a mock database file
    db_file = tmp_path / "mock_memory_db.json"
    backup_dir = tmp_path / "backups"
    
    mock_data = {
        "memories": [{"text": "Hello world", "metadata": {}}],
        "kg_graph": {"nodes": [], "edges": []}
    }
    
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(mock_data, f)
        
    manager = PhoenixBackupManager(db_path=str(db_file), backup_dir=str(backup_dir), max_backups=3)
    
    # 1. Create a backup and check it is valid
    backup_path = manager.create_backup()
    assert os.path.exists(backup_path)
    with open(backup_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
        assert loaded["memories"][0]["text"] == "Hello world"
        
    # 2. Test rotation: Create 4 backups (max is 3)
    import time
    # Create multiple backups with tiny delays to ensure unique timestamps and modification order
    backups = [backup_path]
    for _ in range(3):
        time.sleep(1.0)
        # Update db file modified time or write content to ensure backup is created
        with open(db_file, "w", encoding="utf-8") as f:
            json.dump(mock_data, f)
        backups.append(manager.create_backup())
        
    # Verify exactly 3 backups remain in the backup directory
    remaining_backups = os.listdir(backup_dir)
    assert len(remaining_backups) == 3
    
    # Check that the oldest backup has been deleted (the first backup_path should not be in the list)
    first_backup_name = os.path.basename(backups[0])
    assert first_backup_name not in remaining_backups

def test_backup_api_endpoint(tmp_path):
    with TestClient(app) as client:
        import ai_project.api.main as api_main
        assert api_main.memory_store is not None
        
        orig_db_path = api_main.memory_store.db_path
        
        # Create mock db in tmp_path
        db_file = tmp_path / "api_mock_db.json"
        mock_data = {
            "memories": [],
            "kg_graph": {}
        }
        with open(db_file, "w", encoding="utf-8") as f:
            json.dump(mock_data, f)
            
        api_main.memory_store.db_path = str(db_file)
        
        try:
            token = create_access_token("admin1", "admin", Roles.ADMIN)
            resp = client.post("/api/admin/backup", headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 200
            assert resp.json()["status"] == "success"
            backup_file = resp.json()["backup_file"]
            assert os.path.exists(backup_file)
            # Cleanup created backup file
            if os.path.exists(backup_file):
                os.remove(backup_file)
                # If backups dir empty, remove it too
                backups_dir = os.path.dirname(backup_file)
                if os.path.exists(backups_dir) and not os.listdir(backups_dir):
                    os.rmdir(backups_dir)
        finally:
            api_main.memory_store.db_path = orig_db_path
