"""
Tests for Audit Logging
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.audit.models import AuditAction, AuditLogEntry
from app.audit.logger import hash_clinical_text


class TestAuditModels:
    """Test audit data models"""

    def test_audit_actions_defined(self):
        """All required actions should be defined"""
        assert AuditAction.SUBMIT_CASE
        assert AuditAction.UPLOAD_FILE
        assert AuditAction.LOGIN
        assert AuditAction.LOGOUT

    def test_audit_entry_creation(self):
        """Should create valid audit entry"""
        entry = AuditLogEntry(
            action=AuditAction.SUBMIT_CASE,
            user_id="user123",
            user_email="test@example.com",
            suggested_code="I21.0",
            complexity=5
        )
        assert entry.id is not None
        assert entry.timestamp is not None
        assert entry.action == AuditAction.SUBMIT_CASE
        assert entry.suggested_code == "I21.0"
        assert entry.complexity == 5


class TestClinicalTextHashing:
    """Test privacy-preserving hash function"""

    def test_hash_produces_fixed_length(self):
        """Hash should be 64 chars (SHA-256 hex)"""
        result = hash_clinical_text("test clinical text")
        assert len(result) == 64

    def test_hash_is_deterministic(self):
        """Same input should produce same hash"""
        text = "Patient presents with chest pain"
        hash1 = hash_clinical_text(text)
        hash2 = hash_clinical_text(text)
        assert hash1 == hash2

    def test_different_text_different_hash(self):
        """Different input should produce different hash"""
        hash1 = hash_clinical_text("chest pain")
        hash2 = hash_clinical_text("abdominal pain")
        assert hash1 != hash2

    def test_hash_irreversible(self):
        """Hash should not contain original text"""
        text = "Patient John Smith presents with chest pain"
        result = hash_clinical_text(text)
        assert "John" not in result
        assert "Smith" not in result
        assert "chest" not in result

    def test_empty_string_hashes(self):
        """Empty string should hash without error"""
        result = hash_clinical_text("")
        assert len(result) == 64
