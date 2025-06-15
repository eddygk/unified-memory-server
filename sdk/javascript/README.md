# Unified Memory Server JavaScript SDK

A JavaScript/TypeScript client library for interacting with the Unified Memory Server API.

## Installation

### Browser
```html
<script src="unified-memory-sdk.js"></script>
<script>
    const client = new UnifiedMemoryClient();
</script>
```

### Node.js
```javascript
const { UnifiedMemoryClient, MemorySystem } = require('./unified-memory-sdk.js');
```

### ES6 Modules / TypeScript
```typescript
import { UnifiedMemoryClient, MemorySystem } from './unified-memory-sdk.js';
```

## Quick Start

```javascript
// Create client
const client = new UnifiedMemoryClient({
    baseUrl: 'http://localhost:8000',  // REST API
    mcpUrl: 'http://localhost:9000',   // MCP Server
    timeout: 30000,                    // 30 second timeout
    apiKey: 'your-api-key'             // Optional
});

try {
    // Check system health
    const health = await client.healthCheck();
    console.log('System Status:', health.status);
    
    // Create an entity in Neo4j
    const entity = await client.createEntity(
        'Alice Johnson',
        'Person',
        {
            role: 'Data Scientist',
            department: 'AI Research'
        }
    );
    
    // Create a memory in Redis
    const memory = await client.createMemory(
        'Alice is working on a new machine learning model',
        'default',
        ['machine-learning', 'ai'],
        ['Alice Johnson']
    );
    
    // Create a note in Basic Memory
    const note = await client.createNote(
        'Project Meeting Notes',
        '# Meeting Notes\n\n- Discussed ML model architecture\n- Next steps defined',
        ['meeting', 'project']
    );
    
    // Search across all systems
    const results = await client.searchAll('Alice machine learning');
    console.log('Found results:', results);
    
} catch (error) {
    console.error('Error:', error.message);
}
```

## Features

### Health Monitoring
```javascript
// Check overall system health
const health = await client.healthCheck();

// Check if server is ready for requests  
const ready = await client.readinessCheck();

// Check if server is alive
const alive = await client.livenessCheck();
```

### Neo4j Graph Operations
```javascript
// Create entities
const person = await client.createEntity('John Doe', 'Person', { age: 30 });
const project = await client.createEntity('AI Assistant', 'Project', { status: 'active' });

// Create relationships
const relationship = await client.createRelationship(
    'John Doe', 
    'AI Assistant', 
    'WORKS_ON',
    { role: 'Lead Developer', since: '2024-01-01' }
);

// Search graph
const results = await client.searchGraph('Find all developers working on AI projects');
```

### Redis Memory Operations
```javascript
// Store memories
const memory = await client.createMemory(
    'The team decided to use transformer architecture',
    'project-alpha',
    ['architecture', 'transformers'],
    ['team', 'project-alpha']
);

// Search memories
const results = await client.searchMemories('transformer architecture', 'project-alpha');
```

### Basic Memory Notes
```javascript
// Create notes
const note = await client.createNote(
    'Architecture Decision Record',
    '# ADR-001: Use Transformer Architecture\n\n## Decision\nWe will use...',
    ['adr', 'architecture']
);

// Search notes
const results = await client.searchNotes('transformer decision');
```

### MCP Protocol
```javascript
// Get available tools
const tools = await client.mcpToolsList();

// Call MCP tools
const result = await client.mcpCallTool('create_memory', {
    text: 'Important information',
    namespace: 'default'
});

// Check WebSocket status
const wsStatus = await client.websocketStatus();
```

### Real-time WebSocket Connection
```javascript
// Create WebSocket for real-time updates
const ws = client.createWebSocket(
    (message) => {
        console.log('Received:', message);
    },
    (error) => {
        console.error('WebSocket error:', error);
    }
);

// Send MCP request via WebSocket
ws.send(JSON.stringify({
    jsonrpc: '2.0',
    id: 1,
    method: 'tools/list',
    params: {}
}));

// Close when done
ws.close();
```

### Convenience Methods

#### Smart Storage
```javascript
// Automatically choose the best memory system
await client.storeKnowledge('Alice is a data scientist', 'entity');     // → Neo4j
await client.storeKnowledge('Meeting notes from today', 'document');    // → Basic Memory
await client.storeKnowledge('Important fact about AI', 'general');      // → Redis
```

#### Cross-System Search
```javascript
// Search all memory systems at once
const results = await client.searchAll('machine learning', 10);
// Returns: { neo4j: [...], redis: [...], basic_memory: [...] }
```

## Configuration

### Environment-specific Setup

#### Browser with Authentication
```javascript
const client = new UnifiedMemoryClient({
    baseUrl: 'https://memory.your-domain.com',
    mcpUrl: 'wss://mcp.your-domain.com',
    apiKey: localStorage.getItem('api-key'),
    timeout: 60000
});
```

#### Node.js with Environment Variables
```javascript
const client = new UnifiedMemoryClient({
    baseUrl: process.env.MEMORY_SERVER_URL || 'http://localhost:8000',
    mcpUrl: process.env.MCP_SERVER_URL || 'http://localhost:9000',
    apiKey: process.env.API_KEY,
    timeout: parseInt(process.env.TIMEOUT) || 30000
});
```

## Error Handling

```javascript
try {
    const entity = await client.createEntity('Test', 'Person');
} catch (error) {
    if (error.message.includes('timeout')) {
        console.error('Request timed out');
    } else if (error.message.includes('Network error')) {
        console.error('Network connectivity issue');
    } else {
        console.error('API error:', error.message);
    }
}
```

## TypeScript Support

While the SDK is written in JavaScript, it includes TypeScript-compatible JSDoc types:

```typescript
interface HealthStatus {
    status: string;
    timestamp: number;
    version: string;
    services: Record<string, string>;
}

interface EntityData {
    name: string;
    type: string;
    properties: Record<string, any>;
}

const client = new UnifiedMemoryClient();
const health: HealthStatus = await client.healthCheck();
```

## Browser Compatibility

- Modern browsers (Chrome 76+, Firefox 69+, Safari 12+, Edge 79+)
- Requires ES2018+ support for async/await
- Uses modern fetch API (polyfill may be needed for older browsers)
- WebSocket support for real-time features

## Performance Tips

1. **Reuse client instances** - Create one client and reuse it
2. **Set appropriate timeouts** - Adjust based on your network conditions
3. **Use batch operations** - Combine multiple operations when possible
4. **Handle errors gracefully** - Implement retry logic for network failures

```javascript
// Good: Reuse client
const client = new UnifiedMemoryClient({ timeout: 60000 });

// Batch multiple operations
const promises = [
    client.createEntity('Person1', 'Person'),
    client.createEntity('Person2', 'Person'),
    client.createEntity('Person3', 'Person')
];

const results = await Promise.allSettled(promises);
```

## API Reference

### Constructor Options
- `baseUrl` (string) - REST API base URL
- `mcpUrl` (string) - MCP server base URL
- `timeout` (number) - Request timeout in milliseconds
- `apiKey` (string) - Optional API key for authentication

### Health Methods
- `healthCheck()` - Get system health status
- `readinessCheck()` - Check if server is ready
- `livenessCheck()` - Check if server is alive

### Neo4j Methods
- `createEntity(name, type, properties)` - Create graph entity
- `createRelationship(from, to, type, properties)` - Create relationship
- `searchGraph(query, limit, nodeTypes)` - Search graph

### Redis Memory Methods
- `createMemory(text, namespace, topics, entities, metadata)` - Store memory
- `searchMemories(query, namespace, limit)` - Search memories

### Basic Memory Methods
- `createNote(title, content, tags)` - Create note
- `searchNotes(query, limit)` - Search notes

### MCP Methods
- `mcpHealthCheck()` - Check MCP server
- `mcpToolsList()` - List available tools
- `mcpCallTool(name, args)` - Call MCP tool
- `websocketStatus()` - WebSocket connection status

### Utility Methods
- `storeKnowledge(content, type, system)` - Smart storage
- `searchAll(query, limit)` - Cross-system search
- `createWebSocket(onMessage, onError)` - Real-time connection

## Examples

See the included example usage in the SDK file for more comprehensive examples.