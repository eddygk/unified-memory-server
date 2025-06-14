"""
Test the MCP Server
"""
import pytest
from fastapi.testclient import TestClient
import os

# Set test environment
os.environ["TEST_MODE"] = "true"
os.environ["DISABLE_AUTH"] = "true"

from src.mcp_server import create_mcp_app
from src.memory_selector import MemorySelector, MockCabTracker

@pytest.fixture
def mcp_client():
    """Create test client for MCP server"""
    app = create_mcp_app()
    
    # Manually initialize app state since TestClient doesn't run lifespan
    mock_cab = MockCabTracker()
    memory_selector = MemorySelector(cab_tracker=mock_cab, validate_config=False)
    
    from src.mcp_server import MCPServer
    mcp_server = MCPServer(memory_selector)
    
    app.state.mcp_server = mcp_server
    app.state.memory_selector = memory_selector
    app.state.cab_tracker = mock_cab
    
    return TestClient(app)


def test_mcp_health_endpoint(mcp_client):
    """Test MCP server health check"""
    response = mcp_client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_mcp_tools_list(mcp_client):
    """Test MCP tools list endpoint"""
    request_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    response = mcp_client.post("/sse", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 1
    assert "result" in data
    assert "tools" in data["result"]
    
    tools = data["result"]["tools"]
    tool_names = [tool["name"] for tool in tools]
    
    # Check that all expected tools are present
    expected_tools = [
        "create_memory", "search_memories", "create_entity", 
        "create_relation", "search_graph", "create_note", "search_notes"
    ]
    
    for tool_name in expected_tools:
        assert tool_name in tool_names


def test_mcp_resources_list(mcp_client):
    """Test MCP resources list endpoint"""
    request_data = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "resources/list",
        "params": {}
    }
    
    response = mcp_client.post("/sse", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 2
    assert "result" in data
    assert "resources" in data["result"]
    
    resources = data["result"]["resources"]
    resource_uris = [resource["uri"] for resource in resources]
    
    # Check expected resources
    assert "memory://system/status" in resource_uris
    assert "memory://config/settings" in resource_uris


def test_mcp_resource_read_system_status(mcp_client):
    """Test reading system status resource"""
    request_data = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "resources/read",
        "params": {
            "uri": "memory://system/status"
        }
    }
    
    response = mcp_client.post("/sse", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 3
    assert "result" in data
    assert "contents" in data["result"]
    
    content = data["result"]["contents"][0]
    assert content["uri"] == "memory://system/status"
    assert content["mimeType"] == "application/json"
    assert "text" in content


def test_mcp_tool_call_create_memory(mcp_client):
    """Test calling create_memory tool"""
    request_data = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "create_memory",
            "arguments": {
                "text": "Test memory content",
                "namespace": "test",
                "topics": ["test", "memory"]
            }
        }
    }
    
    response = mcp_client.post("/sse", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 4
    assert "result" in data
    assert "content" in data["result"]


def test_mcp_tool_call_search_memories(mcp_client):
    """Test calling search_memories tool"""
    request_data = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "search_memories",
            "arguments": {
                "query": "test query",
                "namespace": "test",
                "limit": 5
            }
        }
    }
    
    response = mcp_client.post("/sse", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 5
    assert "result" in data
    assert "content" in data["result"]


def test_mcp_tool_call_create_entity(mcp_client):
    """Test calling create_entity tool"""
    request_data = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {
            "name": "create_entity",
            "arguments": {
                "name": "Test Entity",
                "type": "TestType",
                "properties": {"description": "A test entity"}
            }
        }
    }
    
    response = mcp_client.post("/sse", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 6
    assert "result" in data
    assert "content" in data["result"]


def test_mcp_invalid_method(mcp_client):
    """Test calling invalid method returns error"""
    request_data = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "invalid/method",
        "params": {}
    }
    
    response = mcp_client.post("/sse", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 7
    assert "error" in data
    assert data["error"]["code"] == -32601
    assert "Method not found" in data["error"]["message"]


def test_mcp_invalid_json(mcp_client):
    """Test sending invalid JSON returns error"""
    response = mcp_client.post("/sse", data="invalid json")
    assert response.status_code == 400


def test_mcp_openapi_docs(mcp_client):
    """Test MCP server OpenAPI documentation"""
    response = mcp_client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()


def test_mcp_sse_stream_endpoint(mcp_client):
    """Test SSE stream endpoint exists"""
    response = mcp_client.get("/sse/stream")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"