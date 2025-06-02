# API Reference

## Overview

The Unified Memory Server provides both REST API and MCP (Model Context Protocol) endpoints for interacting with the three memory systems. All endpoints require authentication via OAuth2/JWT tokens.

## Base URLs

- **REST API**: `http://10.10.20.100:8000/api/v1`
- **MCP Endpoint**: `http://10.10.20.100:9000/sse`
- **Health Check**: `http://10.10.20.100:8000/health`
- **API Docs**: `http://10.10.20.100:8000/docs` (Swagger/OpenAPI)

## Authentication

### OAuth2 Token Request

```http
POST /auth/token
Content-Type: application/json

{
  "client_id": "your-client-id",
  "client_secret": "your-client-secret",
  "grant_type": "client_credentials",
  "scope": "memories:read memories:write graph:read graph:write"
}
```

#### Response
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "memories:read memories:write graph:read graph:write"
}
```

### Using the Token

Include the token in all subsequent requests:
```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

## Redis Memory Endpoints

### Create Memory

```http
POST /api/v1/memories
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "text": "Important information to remember",
  "namespace": "default",
  "topics": ["topic1", "topic2"],
  "entities": ["Entity1", "Entity2"],
  "metadata": {
    "source": "api",
    "priority": "high",
    "custom_field": "value"
  },
  "session_id": "optional-session-id"
}
```

#### Response
```json
{
  "id": "58lm0xgC576ZbDv1Jmoxc",
  "text": "Important information to remember",
  "namespace": "default",
  "topics": ["topic1", "topic2"],
  "entities": ["Entity1", "Entity2"],
  "created_at": 1717355400,
  "updated_at": 1717355400,
  "metadata": {
    "source": "api",
    "priority": "high",
    "custom_field": "value"
  }
}
```

### Search Memories

```http
GET /api/v1/memories/search
Authorization: Bearer YOUR_TOKEN

Query Parameters:
- q (required): Search query text
- namespace: Filter by namespace
- topics: Comma-separated topic filters
- limit: Maximum results (default: 10, max: 100)
- offset: Pagination offset (default: 0)
- session_id: Filter by session
- created_after: Unix timestamp
- created_before: Unix timestamp
```

#### Response
```json
{
  "memories": [
    {
      "id": "58lm0xgC576ZbDv1Jmoxc",
      "text": "Important information to remember",
      "score": 0.95,
      "namespace": "default",
      "topics": ["topic1", "topic2"],
      "created_at": 1717355400
    }
  ],
  "total": 42,
  "offset": 0,
  "limit": 10
}
```

### Batch Create Memories

```http
POST /api/v1/memories/batch
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "memories": [
    {
      "text": "First memory",
      "topics": ["topic1"]
    },
    {
      "text": "Second memory",
      "topics": ["topic2"]
    }
  ],
  "namespace": "batch-import"
}
```

### Delete Memory

```http
DELETE /api/v1/memories/{memory_id}
Authorization: Bearer YOUR_TOKEN
```

### Hydrate Prompt

```http
POST /api/v1/memories/hydrate
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "text": "User's current query",
  "session_id": "current-session",
  "include_context": true,
  "max_memories": 10
}
```

## Neo4j Graph Endpoints

### Create Entity

```http
POST /api/v1/graph/entities
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "entities": [
    {
      "name": "Project Alpha",
      "type": "Project",
      "observations": [
        "Status: Active",
        "Priority: High",
        "Team Size: 5"
      ],
      "properties": {
        "created_date": "2025-01-01",
        "budget": 100000
      }
    }
  ]
}
```

### Create Relations

```http
POST /api/v1/graph/relations
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "relations": [
    {
      "source": "User123",
      "target": "Project Alpha",
      "relationType": "WORKS_ON",
      "properties": {
        "role": "Developer",
        "since": "2025-01-15"
      }
    }
  ]
}
```

### Query Graph

```http
POST /api/v1/graph/query
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "query": "Find all projects where User123 is involved",
  "query_type": "natural_language",
  "parameters": {}
}
```

#### Alternative Cypher Query
```json
{
  "query": "MATCH (u:User {name: $userName})-[r]->(p:Project) RETURN u, r, p",
  "query_type": "cypher",
  "parameters": {
    "userName": "User123"
  }
}
```

### Search Nodes

```http
GET /api/v1/graph/nodes/search
Authorization: Bearer YOUR_TOKEN

Query Parameters:
- q: Search query
- type: Filter by node type
- limit: Maximum results
```

### Get Node Details

```http
GET /api/v1/graph/nodes/{node_id}
Authorization: Bearer YOUR_TOKEN
```

## Basic Memory Endpoints

### Create Note

```http
POST /api/v1/notes
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "title": "Meeting Notes - Project Alpha",
  "content": "# Meeting Notes\n\n## Attendees\n- John Doe\n- Jane Smith\n\n## Topics...",
  "folder": "projects/alpha",
  "tags": "meeting, project-alpha, planning"
}
```

### Read Note

```http
GET /api/v1/notes/{identifier}
Authorization: Bearer YOUR_TOKEN

Path Parameters:
- identifier: Note title or permalink
```

### Search Notes

```http
GET /api/v1/notes/search
Authorization: Bearer YOUR_TOKEN

Query Parameters:
- q: Search query
- folder: Filter by folder
- tags: Comma-separated tags
- search_type: "text" or "semantic"
```

### Create Canvas

```http
POST /api/v1/canvas
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "title": "System Architecture",
  "folder": "diagrams",
  "nodes": [
    {
      "id": "node1",
      "type": "text",
      "x": 100,
      "y": 100,
      "width": 200,
      "height": 100,
      "text": "API Gateway"
    }
  ],
  "edges": [
    {
      "id": "edge1",
      "fromNode": "node1",
      "toNode": "node2",
      "label": "connects to"
    }
  ]
}
```

## MCP Protocol

### Connection

```http
GET /sse
Authorization: Bearer YOUR_TOKEN
Accept: text/event-stream
```

### Event Types

#### Memory Events
```
event: memory_created
data: {"id": "123", "text": "New memory", "timestamp": 1717355400}

event: memory_updated
data: {"id": "123", "changes": {...}}

event: memory_deleted
data: {"id": "123"}
```

#### Search Events
```
event: search_started
data: {"query_id": "abc", "query": "search text"}

event: search_results
data: {"query_id": "abc", "results": [...], "total": 10}

event: search_completed
data: {"query_id": "abc", "duration_ms": 150}
```

#### Graph Events
```
event: entity_created
data: {"entity": {...}}

event: relation_created
data: {"relation": {...}}

event: graph_updated
data: {"changes": [...]}
```

### Sending Commands

Commands are sent via POST to the MCP endpoint:

```http
POST /mcp/command
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "id": "cmd-123",
  "type": "create_memory",
  "payload": {
    "text": "Memory content",
    "topics": ["topic1"]
  }
}
```

## Error Responses

### Standard Error Format

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Detailed error description",
    "details": {
      "field": "namespace",
      "reason": "Invalid characters in namespace"
    }
  },
  "request_id": "req-abc123",
  "timestamp": 1717355400
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| UNAUTHORIZED | 401 | Missing or invalid authentication |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| INVALID_REQUEST | 400 | Malformed request |
| CONFLICT | 409 | Resource already exists |
| RATE_LIMITED | 429 | Too many requests |
| SERVER_ERROR | 500 | Internal server error |

## Rate Limits

Default rate limits per client:
- 1000 requests per hour
- 100 requests per minute
- 10 concurrent connections

Rate limit headers:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1717359000
```

## Pagination

For endpoints returning lists:

```http
GET /api/v1/memories?limit=20&offset=40
```

Response includes pagination metadata:
```json
{
  "data": [...],
  "pagination": {
    "total": 150,
    "limit": 20,
    "offset": 40,
    "has_next": true,
    "has_prev": true
  }
}
```

## Webhooks

Configure webhooks for real-time notifications:

```http
POST /api/v1/webhooks
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "url": "https://your-server.com/webhook",
  "events": ["memory.created", "entity.updated"],
  "secret": "webhook-secret"
}
```

## SDK Examples

### Python
```python
from unified_memory import Client

client = Client(
    base_url="http://10.10.20.100:8000",
    client_id="your-id",
    client_secret="your-secret"
)

# Automatic token management
memory = client.memories.create(
    text="Important info",
    topics=["topic1"]
)

results = client.memories.search("query text")
```

### JavaScript/TypeScript
```typescript
import { UnifiedMemoryClient } from '@unified-memory/client';

const client = new UnifiedMemoryClient({
  baseUrl: 'http://10.10.20.100:8000',
  clientId: 'your-id',
  clientSecret: 'your-secret'
});

// Async/await pattern
const memory = await client.memories.create({
  text: 'Important info',
  topics: ['topic1']
});

// Promise pattern
client.memories.search('query text')
  .then(results => console.log(results));
```

## Performance Tips

1. **Batch Operations**: Use batch endpoints when creating multiple items
2. **Field Selection**: Request only needed fields using `?fields=id,text`
3. **Caching**: Implement client-side caching for frequently accessed data
4. **Connection Pooling**: Reuse HTTP connections
5. **Compression**: Enable gzip compression with `Accept-Encoding: gzip`

## API Versioning

The API uses URL versioning:
- Current version: `/api/v1`
- Legacy support: Deprecated endpoints return `Sunset` header

```http
Sunset: Sat, 31 Dec 2025 23:59:59 GMT
Deprecation: true
Link: <http://10.10.20.100:8000/api/v2/memories>; rel="successor-version"
```

## OpenAPI Specification

Full OpenAPI 3.0 specification available at:
- JSON: `http://10.10.20.100:8000/openapi.json`
- YAML: `http://10.10.20.100:8000/openapi.yaml`
- Interactive docs: `http://10.10.20.100:8000/docs`

## Testing

### Health Check
```bash
curl http://10.10.20.100:8000/health
```

### API Test Suite
```bash
# Run included test suite
cd unified-memory-server
python -m pytest tests/api/
```

### Postman Collection
Import the Postman collection from `tests/postman/unified-memory-api.json`

## Support

For API issues or feature requests:
- GitHub Issues: https://github.com/eddygk/unified-memory-server/issues
- API Status: http://status.unified-memory.local