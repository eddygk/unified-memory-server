"""
Performance benchmarks for Unified Memory Server
"""
import asyncio
import time
import json
import sys
import os
from typing import List, Dict, Any

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from memory_selector import MemorySelector, MockCabTracker, TaskType
    print("✓ Memory selector imports successful")
    
    # Skip MCP server if FastAPI not available
    try:
        from mcp_server import MCPServer
        MCP_AVAILABLE = True
        print("✓ MCP server imports successful")
    except ImportError:
        MCP_AVAILABLE = False
        print("⚠ MCP server not available (FastAPI dependency missing)")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


class PerformanceBenchmark:
    """Performance benchmarking utilities"""
    
    def __init__(self):
        self.cab_tracker = MockCabTracker()
        self.memory_selector = MemorySelector(cab_tracker=self.cab_tracker, validate_config=False)
        if MCP_AVAILABLE:
            self.mcp_server = MCPServer(self.memory_selector)
        else:
            self.mcp_server = None
    
    async def benchmark_task_analysis(self, num_tasks: int = 1000) -> Dict[str, Any]:
        """Benchmark task analysis performance"""
        print(f"Benchmarking task analysis with {num_tasks} tasks...")
        
        test_tasks = [
            "Create a new memory about artificial intelligence",
            "Find all notes related to machine learning",
            "Add entity named Alice as a Developer",
            "Show relationships between users and projects",
            "Search for documents about Python programming",
            "Store information about a new project called AI Assistant",
            "Retrieve memories about data science",
            "Create relationship between John and Project Alpha"
        ]
        
        start_time = time.time()
        
        for i in range(num_tasks):
            task = test_tasks[i % len(test_tasks)]
            task_type = self.memory_selector.analyze_task(task)
        
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            "operation": "task_analysis",
            "total_tasks": num_tasks,
            "duration_seconds": duration,
            "tasks_per_second": num_tasks / duration,
            "avg_latency_ms": (duration / num_tasks) * 1000
        }
    
    async def benchmark_mcp_requests(self, num_requests: int = 100) -> Dict[str, Any]:
        """Benchmark MCP request processing"""
        if not MCP_AVAILABLE or not self.mcp_server:
            print("Skipping MCP benchmark - not available")
            return {
                "operation": "mcp_requests",
                "skipped": True,
                "reason": "MCP server not available"
            }
            
        print(f"Benchmarking MCP requests with {num_requests} requests...")
        
        test_requests = [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            },
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "create_memory",
                    "arguments": {
                        "text": "Test memory content",
                        "namespace": "test"
                    }
                }
            },
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "resources/list",
                "params": {}
            }
        ]
        
        start_time = time.time()
        
        for i in range(num_requests):
            request = test_requests[i % len(test_requests)]
            response = await self.mcp_server.handle_mcp_request(request)
            # Validate response has correct structure
            assert "jsonrpc" in response
            assert "id" in response
            
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            "operation": "mcp_requests",
            "total_requests": num_requests,
            "duration_seconds": duration,
            "requests_per_second": num_requests / duration,
            "avg_latency_ms": (duration / num_requests) * 1000
        }
    
    async def benchmark_fallback_chains(self, num_operations: int = 50) -> Dict[str, Any]:
        """Benchmark fallback chain operations"""
        print(f"Benchmarking fallback chains with {num_operations} operations...")
        
        def mock_operation(system, task, context):
            # Simulate some processing time
            time.sleep(0.001)  # 1ms
            return {"status": "success", "system": system.value}
        
        start_time = time.time()
        
        for i in range(num_operations):
            task = f"Test operation {i}"
            try:
                result, system, used_fallback = self.memory_selector.execute_with_fallback(
                    task, mock_operation
                )
            except Exception:
                # Expected for some operations in test mode
                pass
        
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            "operation": "fallback_chains",
            "total_operations": num_operations,
            "duration_seconds": duration,
            "operations_per_second": num_operations / duration,
            "avg_latency_ms": (duration / num_operations) * 1000
        }
    
    async def benchmark_websocket_simulation(self, num_connections: int = 10, messages_per_connection: int = 5) -> Dict[str, Any]:
        """Benchmark WebSocket connection simulation"""
        if not MCP_AVAILABLE or not self.mcp_server:
            print("Skipping WebSocket benchmark - not available")
            return {
                "operation": "websocket_simulation",
                "skipped": True,
                "reason": "MCP server not available"
            }
            
        print(f"Simulating {num_connections} WebSocket connections with {messages_per_connection} messages each...")
        
        class MockWebSocket:
            def __init__(self, ws_id):
                self.id = ws_id
                self.is_accepted = False
                
            async def accept(self):
                self.is_accepted = True
                
            async def send_text(self, message):
                pass  # Simulate sending
        
        start_time = time.time()
        
        # Simulate multiple connections
        connection_ids = []
        for i in range(num_connections):
            mock_ws = MockWebSocket(f"test_{i}")
            conn_id = await self.mcp_server.connect_websocket(mock_ws)
            connection_ids.append(conn_id)
        
        # Simulate messages
        total_messages = 0
        for conn_id in connection_ids:
            for j in range(messages_per_connection):
                message = json.dumps({
                    "jsonrpc": "2.0",
                    "id": j,
                    "method": "tools/list",
                    "params": {}
                })
                mock_ws = MockWebSocket(f"test_msg_{j}")
                response = await self.mcp_server.handle_websocket_message(mock_ws, message)
                total_messages += 1
        
        # Clean up connections
        for conn_id in connection_ids:
            await self.mcp_server.disconnect_websocket(conn_id)
        
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            "operation": "websocket_simulation",
            "connections": num_connections,
            "messages_per_connection": messages_per_connection,
            "total_messages": total_messages,
            "duration_seconds": duration,
            "messages_per_second": total_messages / duration,
            "avg_latency_ms": (duration / total_messages) * 1000
        }


async def run_benchmarks():
    """Run all performance benchmarks"""
    print("Starting performance benchmarks...\n")
    
    benchmark = PerformanceBenchmark()
    results = []
    
    try:
        # Task analysis benchmark
        result = await benchmark.benchmark_task_analysis(1000)
        results.append(result)
        print(f"✓ Task Analysis: {result['tasks_per_second']:.2f} tasks/sec, {result['avg_latency_ms']:.2f}ms avg")
        print()
        
        # MCP requests benchmark
        result = await benchmark.benchmark_mcp_requests(100)
        results.append(result)
        if result.get('skipped'):
            print(f"⚠ MCP Requests: Skipped - {result.get('reason', 'Unknown')}")
        else:
            print(f"✓ MCP Requests: {result['requests_per_second']:.2f} req/sec, {result['avg_latency_ms']:.2f}ms avg")
        print()
        
        # Fallback chains benchmark
        result = await benchmark.benchmark_fallback_chains(50)
        results.append(result)
        print(f"✓ Fallback Chains: {result['operations_per_second']:.2f} ops/sec, {result['avg_latency_ms']:.2f}ms avg")
        print()
        
        # WebSocket simulation benchmark
        result = await benchmark.benchmark_websocket_simulation(10, 5)
        results.append(result)
        if result.get('skipped'):
            print(f"⚠ WebSocket Simulation: Skipped - {result.get('reason', 'Unknown')}")
        else:
            print(f"✓ WebSocket Simulation: {result['messages_per_second']:.2f} msg/sec, {result['avg_latency_ms']:.2f}ms avg")
        print()
        
        # Summary
        print("📊 Performance Summary:")
        print("-" * 50)
        for result in results:
            if result.get('skipped'):
                continue
                
            operation = result['operation'].replace('_', ' ').title()
            if 'tasks_per_second' in result:
                throughput = f"{result['tasks_per_second']:.1f} tasks/sec"
            elif 'requests_per_second' in result:
                throughput = f"{result['requests_per_second']:.1f} req/sec"
            elif 'operations_per_second' in result:
                throughput = f"{result['operations_per_second']:.1f} ops/sec"
            elif 'messages_per_second' in result:
                throughput = f"{result['messages_per_second']:.1f} msg/sec"
            else:
                throughput = "N/A"
            
            print(f"{operation:20} | {throughput:15} | {result['avg_latency_ms']:.2f}ms avg")
        
        print()
        print("✅ All benchmarks completed successfully!")
        
        # Save results to file
        with open('performance_results.json', 'w') as f:
            json.dump({
                'timestamp': time.time(),
                'results': results
            }, f, indent=2)
        print("📄 Results saved to performance_results.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_benchmarks())
    exit(0 if success else 1)