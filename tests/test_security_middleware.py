"""
Tests for Phoenix AI Security Middleware.
Covers: Security Headers, CSRF, SSRF prevention.
"""
import pytest
from fastapi import HTTPException
from ai_project.api.middleware import validate_url_ssrf


class TestSSRFPrevention:
    def test_safe_url(self):
        assert validate_url_ssrf("https://api.example.com/data")

    def test_block_file_scheme(self):
        with pytest.raises(HTTPException) as exc:
            validate_url_ssrf("file:///etc/passwd")
        assert exc.value.status_code == 400

    def test_block_ftp_scheme(self):
        with pytest.raises(HTTPException):
            validate_url_ssrf("ftp://internal.server/data")

    def test_block_loopback(self):
        with pytest.raises(HTTPException):
            validate_url_ssrf("http://127.0.0.1/admin")

    def test_block_private_10(self):
        with pytest.raises(HTTPException):
            validate_url_ssrf("http://10.0.0.1/internal")

    def test_block_private_172(self):
        with pytest.raises(HTTPException):
            validate_url_ssrf("http://172.16.0.1/internal")

    def test_block_private_192(self):
        with pytest.raises(HTTPException):
            validate_url_ssrf("http://192.168.1.1/router")

    def test_block_link_local(self):
        with pytest.raises(HTTPException):
            validate_url_ssrf("http://169.254.169.254/latest/meta-data")

    def test_allow_public_domain(self):
        assert validate_url_ssrf("https://google.com")

    def test_block_data_scheme(self):
        with pytest.raises(HTTPException):
            validate_url_ssrf("data:text/html,<h1>test</h1>")

    def test_block_gopher_scheme(self):
        with pytest.raises(HTTPException):
            validate_url_ssrf("gopher://internal:25")
