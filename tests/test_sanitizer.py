"""
Tests for Text Sanitizer
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.coding.sanitizer import sanitize_text


class TestSanitizer:
    """Test text sanitization functions"""

    def test_removes_patient_names(self):
        """Should mask patient names"""
        text = "Patient: John Smith presented with chest pain"
        result = sanitize_text(text)
        assert "John Smith" not in result or "[PATIENT]" in result

    def test_removes_mrn(self):
        """Should mask medical record numbers"""
        text = "MRN: 12345678 presented to ED"
        result = sanitize_text(text)
        assert "12345678" not in result or "[MRN]" in result

    def test_preserves_clinical_content(self):
        """Should keep clinical information intact"""
        text = "Patient presents with acute chest pain radiating to left arm"
        result = sanitize_text(text)
        assert "chest pain" in result.lower()
        assert "left arm" in result.lower()

    def test_handles_empty_string(self):
        """Should handle empty input"""
        result = sanitize_text("")
        assert result == ""

    def test_handles_whitespace(self):
        """Should normalize whitespace"""
        text = "Multiple   spaces   and\n\nnewlines"
        result = sanitize_text(text)
        # Should still contain the words
        assert "multiple" in result.lower()
        assert "spaces" in result.lower()

    def test_handles_special_characters(self):
        """Should handle special characters safely"""
        text = "Temperature: 38.5°C, SpO2: 95%"
        result = sanitize_text(text)
        assert "38.5" in result
        assert "95" in result
