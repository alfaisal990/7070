import os
# Set a secure mock secret key for unit testing to satisfy configuration validation
os.environ["SECRET_KEY"] = "test_run_secure_key_123_456"
os.environ["JWT_SECRET_KEY"] = "test_run_secure_key_123_456"

import pytest
from ai_project.api.auth import create_access_token, Roles


@pytest.fixture
def admin_token():
    """Returns a valid admin JWT access token for tests."""
    return create_access_token("test-admin-id", "admin", Roles.ADMIN)


@pytest.fixture
def developer_token():
    """Returns a valid developer JWT access token for tests."""
    return create_access_token("test-dev-id", "developer", Roles.DEVELOPER)


@pytest.fixture
def user_token():
    """Returns a valid user JWT access token for tests."""
    return create_access_token("test-user-id", "testuser", Roles.USER)


@pytest.fixture
def admin_headers(admin_token):
    """Returns headers with admin Bearer token."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def developer_headers(developer_token):
    """Returns headers with developer Bearer token."""
    return {"Authorization": f"Bearer {developer_token}"}


@pytest.fixture
def user_headers(user_token):
    """Returns headers with user Bearer token."""
    return {"Authorization": f"Bearer {user_token}"}
