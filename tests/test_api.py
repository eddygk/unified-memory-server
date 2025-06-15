"""
Test the FastAPI application
"""
import pytest
from fastapi.testclient import TestClient
import os

# Set test environment
os.environ["TEST_MODE"] = "true"
os.environ["DISABLE_AUTH"] = "true"

from src.main import create_app
from src.memory_selector import MemorySelector, MockCabTracker

@pytest.fixture
def client():
    """Create test client with proper app state"""
    app = create_app()
    
    # Manually initialize app state since TestClient doesn't run lifespan
    mock_cab = MockCabTracker()
    memory_selector = MemorySelector(cab_tracker=mock_cab, validate_config=False)
    
    app.state.memory_selector = memory_selector
    app.state.cab_tracker = mock_cab
    
    return TestClient(app)


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health/")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data
    assert "services" in data
    assert data["version"] == "1.0.0"


def test_health_ready_endpoint(client):
    """Test readiness check endpoint"""
    response = client.get("/health/ready")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ready"
    assert "timestamp" in data


def test_health_live_endpoint(client):
    """Test liveness check endpoint"""
    response = client.get("/health/live")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data


def test_openapi_docs(client):
    """Test OpenAPI documentation is accessible"""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()


def test_openapi_json(client):
    """Test OpenAPI JSON schema"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert data["info"]["title"] == "Unified Memory Server"


def test_create_entity_endpoint_structure(client):
    """Test Neo4j entity creation endpoint exists and has proper structure"""
    # Test with invalid data to check structure (should return 422 for validation error)
    response = client.post("/api/v1/entities", json={})
    assert response.status_code == 422  # Validation error for missing required fields


def test_create_memory_endpoint_structure(client):
    """Test Redis memory creation endpoint exists and has proper structure"""
    # Test with invalid data to check structure (should return 422 for validation error)
    response = client.post("/api/v1/memories", json={})
    assert response.status_code == 422  # Validation error for missing required fields


def test_create_note_endpoint_structure(client):
    """Test Basic Memory note creation endpoint exists and has proper structure"""
    # Test with invalid data to check structure (should return 422 for validation error)
    response = client.post("/api/v1/notes", json={})
    assert response.status_code == 422  # Validation error for missing required fields


def test_api_endpoints_return_proper_errors(client):
    """Test that API endpoints return proper error responses"""
    # Test GET on non-existent entity
    response = client.get("/api/v1/entities/non-existent")
    assert response.status_code in [404, 500]  # Should return not found or server error
    
    # Test GET on non-existent memory
    response = client.get("/api/v1/memories/non-existent")
    assert response.status_code in [404, 500]  # Should return not found or server error
    
    # Test GET on non-existent note
    response = client.get("/api/v1/notes/non-existent")
    assert response.status_code in [404, 500]  # Should return not found or server error