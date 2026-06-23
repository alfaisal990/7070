"""
Tests for Phoenix AI Authentication & Authorization System.
Covers: JWT tokens, RBAC, login, register, refresh, role enforcement.
"""
import pytest
import time
from ai_project.api.auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_jwt,
    create_user, get_user_by_username,
    Roles, ROLE_HIERARCHY, check_route_permission,
    _users_store,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "SecurePass123!"
        hashed = hash_password(password)
        assert verify_password(password, hashed)

    def test_wrong_password(self):
        hashed = hash_password("correct_password")
        assert not verify_password("wrong_password", hashed)

    def test_hash_uniqueness(self):
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        assert h1 != h2  # Different salts

    def test_empty_password(self):
        hashed = hash_password("")
        assert verify_password("", hashed)

    def test_invalid_stored_hash(self):
        assert not verify_password("test", "invalid_hash_format")


class TestJWTTokens:
    def test_create_access_token(self):
        token = create_access_token("user-1", "testuser", Roles.USER)
        assert isinstance(token, str)
        assert token.count(".") == 2

    def test_decode_access_token(self):
        token = create_access_token("user-1", "testuser", Roles.DEVELOPER)
        payload = decode_jwt(token)
        assert payload["sub"] == "user-1"
        assert payload["username"] == "testuser"
        assert payload["role"] == Roles.DEVELOPER
        assert payload["type"] == "access"

    def test_create_refresh_token(self):
        token = create_refresh_token("user-1", "testuser", Roles.USER)
        payload = decode_jwt(token)
        assert payload["type"] == "refresh"

    def test_expired_token(self):
        from ai_project.api import auth
        original = auth.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        auth.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 0  # Expire immediately
        token = create_access_token("user-1", "testuser", Roles.USER)
        time.sleep(1)
        auth.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = original

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_jwt(token)
        assert exc_info.value.status_code == 401

    def test_invalid_token_format(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            decode_jwt("not.a.valid.token.format")

    def test_tampered_token(self):
        from fastapi import HTTPException
        token = create_access_token("user-1", "testuser", Roles.USER)
        # Tamper with the payload
        parts = token.split(".")
        parts[1] = parts[1] + "X"
        tampered = ".".join(parts)
        with pytest.raises(HTTPException):
            decode_jwt(tampered)


class TestRBAC:
    def test_role_hierarchy(self):
        assert ROLE_HIERARCHY[Roles.ADMIN] > ROLE_HIERARCHY[Roles.DEVELOPER]
        assert ROLE_HIERARCHY[Roles.DEVELOPER] > ROLE_HIERARCHY[Roles.OPERATOR]
        assert ROLE_HIERARCHY[Roles.OPERATOR] > ROLE_HIERARCHY[Roles.USER]

    def test_admin_can_access_admin_routes(self):
        assert check_route_permission("/api/admin/backup", Roles.ADMIN)

    def test_user_cannot_access_admin_routes(self):
        assert not check_route_permission("/api/admin/backup", Roles.USER)

    def test_developer_can_access_sandbox(self):
        assert check_route_permission("/api/sandbox/run", Roles.DEVELOPER)

    def test_user_cannot_access_sandbox(self):
        assert not check_route_permission("/api/sandbox/run", Roles.USER)

    def test_admin_inherits_all_permissions(self):
        assert check_route_permission("/api/sandbox/run", Roles.ADMIN)
        assert check_route_permission("/api/chat", Roles.ADMIN)
        assert check_route_permission("/api/admin/backup", Roles.ADMIN)


class TestUserManagement:
    def setup_method(self):
        # Clear store but keep admin
        keys_to_remove = [k for k, v in _users_store.items() if v["username"] != "admin"]
        for k in keys_to_remove:
            del _users_store[k]

    def test_create_user(self):
        user = create_user("newuser", "password123", Roles.USER)
        assert user["username"] == "newuser"
        assert user["role"] == Roles.USER

    def test_duplicate_username(self):
        create_user("dupuser", "password123", Roles.USER)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            create_user("dupuser", "password456", Roles.USER)
        assert exc_info.value.status_code == 409

    def test_get_user_by_username(self):
        create_user("findme", "password123", Roles.DEVELOPER)
        user = get_user_by_username("findme")
        assert user is not None
        assert user["role"] == Roles.DEVELOPER

    def test_get_nonexistent_user(self):
        user = get_user_by_username("nonexistent_user_xyz")
        assert user is None

    def test_default_admin_exists(self):
        admin = get_user_by_username("admin")
        assert admin is not None
        assert admin["role"] == Roles.ADMIN
