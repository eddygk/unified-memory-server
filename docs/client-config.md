# Client Configuration Guide

## Overview

This guide covers how to configure various AI agents and clients to connect to the Unified Memory Server. The server supports multiple connection methods including REST API, MCP (Model Context Protocol), and native client libraries.

## Quick Start

### Server Endpoints
- **REST API**: `http://10.10.20.100:8000`
- **MCP Protocol**: `http://10.10.20.100:9000/sse`
- **Monitoring**: `http://10.10.20.100:3000`

### Authentication
All clients require OAuth2 authentication. Obtain your credentials from your administrator:
- Client ID
- Client Secret
- Namespace (for multi-tenant isolation)

## Claude Desktop Configuration

### Windows Setup

1. **Install MCP Proxy Client**
   ```powershell
   # Download MCP proxy client
   git clone https://github.com/eddygk/unified-memory-server.git
   cd unified-memory-server/clients/mcp-proxy
   npm install
   ```

2. **Configure Claude Desktop**
   
   Edit `%APPDATA%\Claude\config.json`:
   ```json
   {
     "mcpServers": {
       "unified-memory": {
         "command": "node",
         "args": ["C:\\path\\to\\memory-client\\index.js"],
         "env": {
           "MEMORY_SERVER_URL": "http://10.10.20.100:9000/sse",
           "AUTH0_CLIENT_ID": "your-client-id",
           "AUTH0_CLIENT_SECRET": "your-client-secret",
           "NAMESPACE": "claude-windows",
           "LOG_LEVEL": "info"
         }
       }
     }
   }
   ```

3. **Test Connection**
   - Restart Claude Desktop
   - Check MCP connection status in Claude settings
   - Try: "Store this in memory: Test message from Windows"

### macOS Setup

1. **Install MCP Proxy Client**
   ```bash
   # Clone repository
   git clone https://github.com/eddygk/unified-memory-server.git
   cd unified-memory-server/clients/mcp-proxy
   npm install
   ```

2. **Configure Claude Desktop**
   
   Edit `~/Library/Application Support/Claude/config.json`:
   ```json
   {
     "mcpServers": {
       "unified-memory": {
         "command": "node",
         "args": ["/Users/username/memory-client/index.js"],
         "env": {
           "MEMORY_SERVER_URL": "http://10.10.20.100:9000/sse",
           "AUTH0_CLIENT_ID": "your-client-id",
           "AUTH0_CLIENT_SECRET": "your-client-secret",
           "NAMESPACE": "claude-mac",
           "LOG_LEVEL": "info"
         }
       }
     }
   }
   ```

3. **Enable Permissions**
   - System Preferences → Security & Privacy → Privacy
   - Grant Claude Desktop network access if prompted

### Linux Setup (Windsurf)

For Windsurf or other Linux-based Claude implementations:

```bash
# Install dependencies
sudo apt update
sudo apt install nodejs npm

# Clone and setup
git clone https://github.com/eddygk/unified-memory-server.git
cd unified-memory-server/clients/mcp-proxy
npm install

# Configure environment
export MEMORY_SERVER_URL="http://10.10.20.100:9000/sse"
export AUTH0_CLIENT_ID="your-client-id"
export AUTH0_CLIENT_SECRET="your-client-secret"
export NAMESPACE="claude-linux"
```

## Python Client

### Installation

```bash
pip install unified-memory-client
```

### Basic Usage

```python
from unified_memory_client import UnifiedMemoryClient

# Initialize client
client = UnifiedMemoryClient(
    base_url="http://10.10.20.100:8000",
    client_id="your-client-id",
    client_secret="your-client-secret",
    namespace="python-agent"
)

# Authenticate
client.authenticate()

# Store memory
client.create_memory(
    text="Important information to remember",
    topics=["topic1", "topic2"],
    entity_type="observation"
)

# Search memories
results = client.search_memory(
    query="important information",
    limit=5,
    namespace="python-agent"
)

# Neo4j operations
client.create_entity(
    name="Project Alpha",
    entity_type="Project",
    observations=["Status: Active", "Priority: High"]
)

client.create_relation(
    source="User123",
    target="Project Alpha",
    relation_type="WORKS_ON"
)

# Natural language query
result = client.query_graph(
    "Find all projects that User123 works on",
    query_type="natural_language"
)
```

### Advanced Features

```python
# Batch operations
memories = [
    {"text": "Memory 1", "topics": ["topic1"]},
    {"text": "Memory 2", "topics": ["topic2"]}
]
client.batch_create_memories(memories)

# Session management
with client.session("conversation-123") as session:
    session.add_message("User question here")
    response = session.get_context()
    
# Streaming responses
for chunk in client.stream_search("query", real_time=True):
    print(chunk)
```

## JavaScript/TypeScript Client

### Installation

```bash
npm install @unified-memory/client
# or
yarn add @unified-memory/client
```

### Usage

```typescript
import { UnifiedMemoryClient } from '@unified-memory/client';

// Initialize client
const client = new UnifiedMemoryClient({
  baseUrl: 'http://10.10.20.100:8000',
  clientId: 'your-client-id',
  clientSecret: 'your-client-secret',
  namespace: 'js-agent'
});

// Authenticate
await client.authenticate();

// Store memory
await client.createMemory({
  text: 'Important information',
  topics: ['topic1'],
  entities: ['Entity1']
});

// Search with filters
const results = await client.searchMemory({
  query: 'important',
  filters: {
    topics: { any: ['topic1', 'topic2'] },
    created_at: { gt: Date.now() - 86400000 }
  },
  limit: 10
});

// GraphQL-style queries for Neo4j
const graphResult = await client.graphQuery({
  query: `
    MATCH (u:User)-[:WORKS_ON]->(p:Project)
    WHERE u.name = $userName
    RETURN p
  `,
  parameters: { userName: 'User123' }
});
```

## REST API Direct Access

### Authentication Flow

```bash
# Get access token
curl -X POST http://10.10.20.100:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "your-client-id",
    "client_secret": "your-client-secret",
    "grant_type": "client_credentials"
  }'

# Response:
# {
#   "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "token_type": "Bearer",
#   "expires_in": 3600
# }
```

### API Examples

```bash
# Create memory
curl -X POST http://10.10.20.100:8000/api/v1/memories \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Important information",
    "namespace": "api-test",
    "topics": ["test"],
    "metadata": {
      "source": "manual",
      "priority": "high"
    }
  }'

# Search memories
curl -X GET "http://10.10.20.100:8000/api/v1/memories/search?q=important&limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Neo4j query
curl -X POST http://10.10.20.100:8000/api/v1/graph/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "MATCH (n:User) RETURN n LIMIT 5",
    "type": "cypher"
  }'
```

## MCP Protocol Details

### Connection Flow

1. **Initial Connection**
   ```
   GET http://10.10.20.100:9000/sse
   Headers:
     Authorization: Bearer <token>
     Accept: text/event-stream
   ```

2. **Event Stream Format**
   ```
   event: memory_created
   data: {"id": "123", "text": "Memory content", "timestamp": 1234567890}

   event: search_results
   data: {"query": "search term", "results": [...], "total": 10}
   ```

3. **Command Protocol**
   ```json
   {
     "type": "command",
     "action": "create_memory",
     "payload": {
       "text": "Memory content",
       "topics": ["topic1"]
     }
   }
   ```

## Multi-Agent Configuration

### Namespace Isolation

Each agent should use a unique namespace to prevent data collision:

```python
# Agent 1: Customer Service Bot
cs_client = UnifiedMemoryClient(
    namespace="customer-service",
    # ... other config
)

# Agent 2: Technical Support Bot
ts_client = UnifiedMemoryClient(
    namespace="tech-support",
    # ... other config
)

# Shared namespace for cross-agent data
shared_client = UnifiedMemoryClient(
    namespace="shared-knowledge",
    # ... other config
)
```

### Cross-Agent Communication

```python
# Agent 1 stores information
cs_client.create_memory(
    text="Customer reported issue #1234",
    namespace="shared-knowledge",
    topics=["issues", "customer-feedback"]
)

# Agent 2 retrieves information
issues = ts_client.search_memory(
    query="issue #1234",
    namespace="shared-knowledge"
)
```

## Performance Optimization

### Connection Pooling

```python
# Python example
from unified_memory_client import UnifiedMemoryClient, ConnectionPool

pool = ConnectionPool(
    max_connections=10,
    timeout=30,
    retry_count=3
)

client = UnifiedMemoryClient(
    connection_pool=pool,
    # ... other config
)
```

### Batch Operations

```javascript
// JavaScript example
const batchSize = 100;
const memories = getLargeDataset();

for (let i = 0; i < memories.length; i += batchSize) {
  const batch = memories.slice(i, i + batchSize);
  await client.batchCreate(batch);
}
```

### Caching Strategy

```python
# Local caching for frequently accessed data
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_user_preferences(user_id):
    return client.search_memory(
        query=f"user:{user_id} preferences",
        namespace="user-data",
        limit=1
    )
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Verify server is running: `curl http://10.10.20.100:8000/health`
   - Check firewall rules
   - Verify network connectivity: `ping 10.10.20.100`

2. **Authentication Failures**
   - Verify client credentials
   - Check token expiration
   - Validate OAuth2 configuration

3. **Timeout Errors**
   - Increase client timeout settings
   - Check server load
   - Verify network latency

### Debug Mode

Enable debug logging in clients:

```python
# Python
import logging
logging.basicConfig(level=logging.DEBUG)
client = UnifiedMemoryClient(debug=True)
```

```javascript
// JavaScript
const client = new UnifiedMemoryClient({
  debug: true,
  logger: console
});
```

### Health Checks

```python
# Python health check script
def check_memory_server():
    try:
        # Check API
        response = requests.get("http://10.10.20.100:8000/health")
        api_status = response.json()
        
        # Check MCP
        mcp_response = requests.get("http://10.10.20.100:9000/health")
        mcp_status = mcp_response.json()
        
        return {
            "api": api_status,
            "mcp": mcp_status,
            "overall": "healthy"
        }
    except Exception as e:
        return {
            "error": str(e),
            "overall": "unhealthy"
        }
```

## Security Best Practices

1. **Credential Management**
   - Never hardcode credentials
   - Use environment variables or secure vaults
   - Rotate credentials regularly

2. **Network Security**
   - Use HTTPS in production
   - Implement IP whitelisting
   - Enable rate limiting

3. **Data Privacy**
   - Encrypt sensitive data before storage
   - Use appropriate namespaces for isolation
   - Implement data retention policies

## Migration from Other Systems

### From Local Storage

```python
# Migrate from local JSON files
import json
import glob

for file_path in glob.glob("memories/*.json"):
    with open(file_path, 'r') as f:
        data = json.load(f)
        
    client.create_memory(
        text=data['content'],
        topics=data.get('tags', []),
        metadata=data.get('metadata', {})
    )
```

### From Other Memory Systems

See [Migration Guide](migration.md) for detailed instructions on migrating from:
- LangChain memory
- OpenAI Assistants
- Custom implementations

## Support Resources

- API Documentation: http://10.10.20.100:8000/docs
- GitHub Issues: https://github.com/eddygk/unified-memory-server/issues
- Community Discord: [Join here](https://discord.gg/unified-memory)