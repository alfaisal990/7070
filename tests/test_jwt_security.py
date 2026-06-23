import os
import pytest
from pydantic import ValidationError
from task_manager.app.config import Settings

def test_jwt_security_validation():
    # Save original env and pop it
    orig_env = os.environ.pop("SECRET_KEY", None)
    
    try:
        # 1. Missing SECRET_KEY should fail validation
        with pytest.raises(ValidationError):
            Settings(_env_file=None, DATABASE_URL="sqlite://")
    finally:
        # Restore env
        if orig_env is not None:
            os.environ["SECRET_KEY"] = orig_env
            
    # 2. Default insecure keys must fail validation
    with pytest.raises(ValidationError):
        Settings(_env_file=None, DATABASE_URL="sqlite://", SECRET_KEY="supersecretkeychangeinproduction")
        
    with pytest.raises(ValidationError):
        Settings(_env_file=None, DATABASE_URL="sqlite://", SECRET_KEY="yoursecretkeyherechangeinproduction123")
        
    # 3. A secure key should succeed
    settings = Settings(_env_file=None, DATABASE_URL="sqlite://", SECRET_KEY="a_very_secure_and_random_string_123_456!")
    assert settings.SECRET_KEY == "a_very_secure_and_random_string_123_456!"
