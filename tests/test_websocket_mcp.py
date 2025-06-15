"""
Test WebSocket functionality for MCP server
"""
import json
import asyncio
from unittest.mock import Mock, AsyncMock
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_server import MCPServer
from memory_selector import MemorySelector, MockCabTracker


class MockWebSocket:
    """Mock WebSocket for testing"""
    def __init__(self):
        self.messages_sent = []
        self.is_accepted = False
        
    async def accept(self):
        self.is_accepted = True
        
    async def send_text(self, message: str):
        self.messages_sent.append(message)
        
    async def receive_text(self) -> str:
        # Mock receiving a tools/list request
        return json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        })


async def test_websocket_connection():
    """Test WebSocket connection handling"""
    print("Testing WebSocket connection...")
    
    # Setup
    cab_tracker = MockCabTracker()
    memory_selector = MemorySelector(cab_tracker=cab_tracker, validate_config=False)
    mcp_server = MCPServer(memory_selector)
    
    # Test connection
    mock_websocket = MockWebSocket()
    connection_id = await mcp_server.connect_websocket(mock_websocket)
    
    assert mock_websocket.is_accepted
    assert connection_id in mcp_server.active_connections
    assert len(mcp_server.active_connections) == 1
    
    print(f"✓ WebSocket connection established: {connection_id}")
    
    # Test disconnection
    await mcp_server.disconnect_websocket(connection_id)
    assert connection_id not in mcp_server.active_connections
    assert len(mcp_server.active_connections) == 0
    
    print("✓ WebSocket disconnection handled")


async def test_websocket_message_handling():
    """Test WebSocket message processing"""
    print("Testing WebSocket message handling...")
    
    # Setup
    cab_tracker = MockCabTracker()
    memory_selector = MemorySelector(cab_tracker=cab_tracker, validate_config=False)
    mcp_server = MCPServer(memory_selector)
    
    mock_websocket = MockWebSocket()
    
    # Test valid JSON message
    message = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    })
    
    response = await mcp_server.handle_websocket_message(mock_websocket, message)
    
    assert response is not None
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1
    assert "result" in response
    assert "tools" in response["result"]
    
    print("✓ Valid JSON message processed successfully")
    
    # Test invalid JSON
    invalid_message = "invalid json"
    response = await mcp_server.handle_websocket_message(mock_websocket, invalid_message)
    
    assert response is not None
    assert "error" in response
    assert response["error"]["code"] == -32700
    
    print("✓ Invalid JSON handled with proper error")


async def test_broadcast_event():
    """Test event broadcasting to multiple WebSocket connections"""
    print("Testing event broadcasting...")
    
    # Setup
    cab_tracker = MockCabTracker()
    memory_selector = MemorySelector(cab_tracker=cab_tracker, validate_config=False)
    mcp_server = MCPServer(memory_selector)
    
    # Connect multiple mock WebSockets
    websockets = []
    connection_ids = []
    
    for i in range(3):
        mock_websocket = MockWebSocket()
        connection_id = await mcp_server.connect_websocket(mock_websocket)
        websockets.append(mock_websocket)
        connection_ids.append(connection_id)
    
    # Broadcast an event
    test_event = {
        "type": "memory_update",
        "data": {"message": "Test broadcast"}
    }
    
    await mcp_server.broadcast_event(test_event)
    
    # Check that all WebSockets received the message
    expected_message = json.dumps(test_event)
    for websocket in websockets:
        assert len(websocket.messages_sent) == 1
        assert websocket.messages_sent[0] == expected_message
    
    print(f"✓ Event broadcasted to {len(websockets)} connections")


async def run_all_tests():
    """Run all WebSocket tests"""
    print("Starting WebSocket MCP tests...\n")
    
    try:
        await test_websocket_connection()
        print()
        
        await test_websocket_message_handling()
        print()
        
        await test_broadcast_event()
        print()
        
        print("✅ All WebSocket tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)