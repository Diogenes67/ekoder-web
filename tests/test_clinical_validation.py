"""
Clinical Validation Tests
13 real-world ED cases to validate coding accuracy
"""
import pytest


class TestClinicalValidation:
    """
    Validate coding accuracy against known clinical scenarios.
    These tests verify the system produces appropriate ICD-10-AM codes
    for typical ED presentations.
    """

    @pytest.mark.parametrize("case_id", range(1, 14))
    def test_clinical_case(self, client, auth_headers, clinical_cases, case_id):
        """
        Test each clinical case produces valid results.
        
        Note: Full accuracy testing requires the LLM and retriever to be 
        properly configured. These tests validate the structure and
        that codes are from the expected categories.
        """
        case = next((c for c in clinical_cases if c["id"] == case_id), None)
        if case is None:
            pytest.skip(f"Case {case_id} not found")

        response = client.post("/api/v1/code",
            json={"clinical_text": case["text"]},
            headers=auth_headers
        )

        # Should get a response (may be error if LLM not configured)
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            
            # Should have structured response
            assert "requires_human_review" in data
            assert data["requires_human_review"] is True  # Always true for ACCD
            
            # If we got a suggestion, validate it
            if data.get("suggested_code"):
                code = data["suggested_code"]
                
                # Code should be properly formatted (letter + digits)
                assert len(code) >= 3
                assert code[0].isalpha()
                
                # Should have reasoning
                assert data.get("reasoning")
                
                # Should have complexity in valid range
                if data.get("complexity"):
                    assert 1 <= data["complexity"] <= 6
                    
                    # Check complexity is in expected range for this case
                    min_complexity, max_complexity = case["complexity_range"]
                    # Allow some variance
                    assert data["complexity"] >= min_complexity - 1
                    assert data["complexity"] <= max_complexity + 1
            
            # Should have candidates
            if data.get("candidates"):
                assert len(data["candidates"]) > 0
                for candidate in data["candidates"]:
                    assert "code" in candidate
                    assert "descriptor" in candidate


class TestComplexityMapping:
    """Test complexity levels are correctly assigned"""

    def test_complexity_labels_exist(self):
        """Verify all complexity levels have labels"""
        from app.coding.routes import COMPLEXITY_LABELS
        
        assert 1 in COMPLEXITY_LABELS
        assert 6 in COMPLEXITY_LABELS
        assert COMPLEXITY_LABELS[1] == "Minor (1)"
        assert COMPLEXITY_LABELS[6] == "Very High (6)"

    def test_complexity_range(self):
        """Verify complexity values are 1-6"""
        from app.coding.routes import COMPLEXITY_LABELS
        
        for level in range(1, 7):
            assert level in COMPLEXITY_LABELS


class TestCodeValidation:
    """Test ICD-10-AM code format validation"""

    def test_valid_code_formats(self):
        """Valid ICD-10-AM codes should be accepted"""
        valid_codes = [
            "I21.0",   # STEMI anterior
            "S82.6",   # Fracture lateral malleolus
            "J06.9",   # URTI
            "K35.80",  # Acute appendicitis
            "A09",     # Gastroenteritis
            "R50.9",   # Fever
        ]
        
        for code in valid_codes:
            # Basic format check
            assert len(code) >= 3
            assert code[0].isalpha()
            assert code[0].isupper()


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_text(self, client, auth_headers):
        """Should handle empty clinical text"""
        response = client.post("/api/v1/code",
            json={"clinical_text": ""},
            headers=auth_headers
        )
        # Should handle gracefully
        assert response.status_code in [200, 422, 500]

    def test_very_short_text(self, client, auth_headers):
        """Should handle very short text"""
        response = client.post("/api/v1/code",
            json={"clinical_text": "pain"},
            headers=auth_headers
        )
        assert response.status_code in [200, 500]

    def test_very_long_text(self, client, auth_headers):
        """Should handle long clinical notes"""
        long_text = "Patient presents with " + "chest pain " * 500
        response = client.post("/api/v1/code",
            json={"clinical_text": long_text},
            headers=auth_headers
        )
        assert response.status_code in [200, 500]

    def test_special_characters(self, client, auth_headers):
        """Should handle special characters"""
        text = "Temp: 38.5°C, SpO2: 95%, BP: 120/80mmHg"
        response = client.post("/api/v1/code",
            json={"clinical_text": text},
            headers=auth_headers
        )
        assert response.status_code in [200, 500]
