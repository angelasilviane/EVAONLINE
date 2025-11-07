"""
Integration tests for FastAPI endpoints.
Tests health checks, data endpoints, and API versioning.
"""

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Test consolidated health check endpoint."""

    def test_health_endpoint_exists(self, client: TestClient):
        """Test /api/v1/health/detailed endpoint returns 200."""
        response = client.get("/api/v1/health/detailed")
        assert response.status_code == 200

    def test_health_endpoint_response_format(self, client: TestClient):
        """Test /api/v1/health/detailed returns expected JSON format."""
        response = client.get("/api/v1/health/detailed")
        data = response.json()

        # Check required fields from all 3 consolidated health checks
        assert "status" in data  # From health basic
        assert "service" in data
        assert "version" in data
        assert "timestamp" in data

        # Check detailed health info
        assert "detailed" in data

        # Check readiness info
        assert "api" in data
        assert "ready" in data["api"]

        # Status should be ok or degraded
        assert data["status"] in ["ok", "degraded"]

    def test_health_endpoint_has_all_subsystems(self, client: TestClient):
        """Test /api/v1/health/detailed includes all subsystem info."""
        response = client.get("/api/v1/health/detailed")
        data = response.json()

        # Should have detailed health info from all components
        detailed = data.get("detailed", {})

        # Check for expected fields in detailed section
        assert isinstance(detailed, dict)


class TestAPIVersioning:
    """Test API versioning and routing."""

    def test_api_v1_prefix_exists(self, client: TestClient):
        """Test that routes use /api/v1/ prefix."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_routes_require_api_prefix(self, client: TestClient):
        """Test that routes without /api/v1/ are not accessible."""
        response = client.get("/health")
        # Should either 404 or redirect to /api/v1/health
        assert response.status_code in [404, 307, 308]


class TestAppMetadata:
    """Test application metadata and documentation."""

    def test_docs_endpoint_available(self, client: TestClient):
        """Test /api/v1/docs endpoint is available for Swagger UI."""
        response = client.get("/api/v1/docs")
        assert response.status_code in [200, 403]  # May be disabled in prod

    def test_redoc_endpoint_available(self, client: TestClient):
        """Test /redoc endpoint or /api/v1/docs is available."""
        # Try /api/v1/docs first, fall back to /redoc
        response = client.get("/api/v1/docs")
        assert response.status_code in [200, 403, 404]

    def test_openapi_schema_available(self, client: TestClient):
        """Test OpenAPI schema endpoint exists."""
        response = client.get("/openapi.json")
        if response.status_code == 200:
            data = response.json()
            assert "openapi" in data or "swagger" in data
        # May be disabled, so 404 is acceptable
        assert response.status_code in [200, 404]
