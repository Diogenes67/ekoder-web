"""
Tests for Authentication
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.auth.utils import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_token
)


class TestPasswordHashing:
    """Test password hashing functions"""

    def test_hash_password(self):
        """Should create a hash different from original"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 20

    def test_verify_correct_password(self):
        """Should verify correct password"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_reject_wrong_password(self):
        """Should reject incorrect password"""
        password = "testpassword123"
        wrong = "wrongpassword"
        hashed = get_password_hash(password)
        assert verify_password(wrong, hashed) is False

    def test_different_hashes_same_password(self):
        """Same password should produce different hashes (salting)"""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2


class TestJWT:
    """Test JWT token functions"""

    def test_create_token(self):
        """Should create a valid token"""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)
        assert token is not None
        assert len(token) > 50

    def test_decode_valid_token(self):
        """Should decode a valid token"""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)
        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["sub"] == "user123"
        assert decoded["email"] == "test@example.com"

    def test_decode_invalid_token(self):
        """Should return None for invalid token"""
        result = decode_token("invalid.token.here")
        assert result is None

    def test_token_contains_expiry(self):
        """Token should have expiration"""
        data = {"sub": "user123"}
        token = create_access_token(data)
        decoded = decode_token(token)
        assert "exp" in decoded
