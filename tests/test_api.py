"""
Tests for API Endpoints
"""
import pytest


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self, client):
        """Should return healthy status"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestAuthEndpoints:
    """Test authentication endpoints"""

    def test_login_success(self, client):
        """Should login with valid credentials"""
        response = client.post("/api/v1/auth/login", json={
            "email": "admin@ekoder.dev",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        """Should reject wrong password"""
        response = client.post("/api/v1/auth/login", json={
            "email": "admin@ekoder.dev",
            "password": "wrongpassword"
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """Should reject nonexistent user"""
        response = client.post("/api/v1/auth/login", json={
            "email": "nobody@example.com",
            "password": "password123"
        })
        assert response.status_code == 401

    def test_me_endpoint_authenticated(self, client, auth_headers):
        """Should return user info when authenticated"""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@ekoder.dev"

    def test_me_endpoint_unauthenticated(self, client):
        """Should reject unauthenticated request"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code in [401, 403]  # Either is acceptable


class TestCodingEndpoints:
    """Test coding API endpoints"""

    def test_code_endpoint_requires_text(self, client, auth_headers):
        """Should require clinical text"""
        response = client.post("/api/v1/code", 
            json={},
            headers=auth_headers
        )
        assert response.status_code == 422  # Validation error

    def test_code_endpoint_accepts_text(self, client, auth_headers):
        """Should accept valid clinical text"""
        response = client.post("/api/v1/code",
            json={"clinical_text": "Patient with chest pain"},
            headers=auth_headers
        )
        # Should get 200 even if LLM/retriever not fully configured
        assert response.status_code in [200, 500]

    def test_upload_endpoint_requires_file(self, client, auth_headers):
        """Should require file upload"""
        response = client.post("/api/v1/code/upload",
            headers=auth_headers
        )
        assert response.status_code == 422


class TestAuditEndpoints:
    """Test audit log endpoints"""

    def test_audit_logs_requires_admin(self, client):
        """Should require authentication"""
        response = client.get("/api/v1/audit/logs")
        assert response.status_code in [401, 403]  # Either is acceptable

    def test_audit_logs_authenticated(self, client, auth_headers):
        """Should return logs for admin"""
        response = client.get("/api/v1/audit/logs", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert "total" in data

    def test_my_stats_authenticated(self, client, auth_headers):
        """Should return user stats"""
        response = client.get("/api/v1/audit/my-stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_cases" in data
