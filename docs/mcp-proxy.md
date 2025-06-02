# MCP Proxy Client Guide

## Overview

The MCP (Model Context Protocol) Proxy Client enables Claude Desktop and other MCP-compatible AI assistants to connect to the Unified Memory Server. It handles OAuth2 authentication, maintains persistent connections, and translates between MCP commands and the memory server API.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude Desktop                          │
│                  (Windows/Mac/Linux)                        │
└───────────────────────┬─────────────────────────────────────┘
                        │ MCP Protocol
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   MCP Proxy Client                          │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   OAuth2    │  │   Command    │  │   Event      │      │
│  │   Handler   │  │   Router     │  │   Stream     │      │
│  └─────────────┘  └──────────────┘  └──────────────┘      │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTPS + SSE
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Unified Memory Server API                      │
│                  10.10.20.100:9000                         │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites
- Node.js 18+ and npm
- Claude Desktop installed
- OAuth2 credentials from your administrator

### Install from npm
```bash
npm install -g @unified-memory/mcp-proxy
```

### Install from Source
```bash
git clone https://github.com/eddygk/unified-memory-server.git
cd unified-memory-server/clients/mcp-proxy
npm install
npm link
```

## Configuration

### Claude Desktop Configuration

#### Windows
Location: `%APPDATA%\Claude\config.json`

```json
{
  "mcpServers": {
    "unified-memory": {
      "command": "unified-memory-mcp",
      "args": ["--config", "C:\\Users\\YourUser\\.unified-memory\\config.json"],
      "env": {
        "NODE_ENV": "production"
      }
    }
  }
}
```

#### macOS
Location: `~/Library/Application Support/Claude/config.json`

```json
{
  "mcpServers": {
    "unified-memory": {
      "command": "unified-memory-mcp",
      "args": ["--config", "~/.unified-memory/config.json"],
      "env": {
        "NODE_ENV": "production"
      }
    }
  }
}
```

#### Linux
Location: `~/.config/Claude/config.json`

```json
{
  "mcpServers": {
    "unified-memory": {
      "command": "unified-memory-mcp",
      "args": ["--config", "~/.config/unified-memory/config.json"],
      "env": {
        "NODE_ENV": "production"
      }
    }
  }
}
```

### Proxy Configuration File

Create configuration file at the specified location:

```json
{
  "server": {
    "url": "http://10.10.20.100:9000",
    "sseEndpoint": "/sse",
    "timeout": 30000
  },
  "auth": {
    "clientId": "your-client-id",
    "clientSecret": "your-client-secret",
    "tokenEndpoint": "http://10.10.20.100:8000/auth/token",
    "refreshBeforeExpiry": 300
  },
  "client": {
    "namespace": "claude-desktop",
    "reconnectInterval": 5000,
    "maxReconnectAttempts": 10
  },
  "logging": {
    "level": "info",
    "file": "~/.unified-memory/logs/mcp-proxy.log"
  }
}
```

### Environment Variables

Alternative to config file:

```bash
export UNIFIED_MEMORY_URL="http://10.10.20.100:9000"
export UNIFIED_MEMORY_CLIENT_ID="your-client-id"
export UNIFIED_MEMORY_CLIENT_SECRET="your-client-secret"
export UNIFIED_MEMORY_NAMESPACE="claude-desktop"
export UNIFIED_MEMORY_LOG_LEVEL="debug"
```

## MCP Commands

### Memory Operations

#### Store Memory
```
Command: store_memory
Parameters:
  - text: string (required)
  - topics: string[] (optional)
  - entities: string[] (optional)
  - metadata: object (optional)

Example:
"Store this in memory: The user prefers dark mode interfaces"
```

#### Search Memory
```
Command: search_memory
Parameters:
  - query: string (required)
  - limit: number (optional, default: 10)
  - namespace: string (optional)
  - filters: object (optional)

Example:
"Search my memories for user preferences"
```

#### Hydrate Context
```
Command: hydrate_context
Parameters:
  - text: string (required)
  - session_id: string (optional)
  - include_graph: boolean (optional)

Example:
"What do you know about my project preferences?"
```

### Graph Operations

#### Create Entity
```
Command: create_entity
Parameters:
  - name: string (required)
  - type: string (required)
  - observations: string[] (optional)
  - properties: object (optional)

Example:
"Create entity: Project Alpha (type: Project) with status Active"
```

#### Create Relation
```
Command: create_relation
Parameters:
  - source: string (required)
  - target: string (required)
  - relationType: string (required)
  - properties: object (optional)

Example:
"Connect User123 to Project Alpha with relation WORKS_ON"
```

#### Query Graph
```
Command: query_graph
Parameters:
  - query: string (required)
  - query_type: "natural_language" | "cypher" (optional)
  - parameters: object (optional)

Example:
"Find all projects I'm working on"
```

### Note Operations

#### Create Note
```
Command: create_note
Parameters:
  - title: string (required)
  - content: string (required)
  - folder: string (optional)
  - tags: string (optional)

Example:
"Create a note titled 'Meeting Notes' in the projects folder"
```

#### Search Notes
```
Command: search_notes
Parameters:
  - query: string (required)
  - search_type: "text" | "semantic" (optional)
  - folder: string (optional)

Example:
"Find all notes about architecture decisions"
```

## Event Handling

The proxy client receives real-time events from the server:

### Memory Events
```javascript
// Event handler in proxy
client.on('memory_created', (data) => {
  // Forward to Claude
  mcp.notify('memory.created', {
    id: data.id,
    text: data.text,
    timestamp: data.created_at
  });
});

client.on('memory_updated', (data) => {
  mcp.notify('memory.updated', data);
});
```

### Search Events
```javascript
client.on('search_started', (data) => {
  mcp.notify('search.started', {
    queryId: data.query_id,
    query: data.query
  });
});

client.on('search_results', (data) => {
  mcp.notify('search.results', {
    queryId: data.query_id,
    results: data.results,
    total: data.total
  });
});
```

## Advanced Features

### Custom Command Handlers

```javascript
// Register custom command
mcp.registerCommand('analyze_memory_usage', async (params) => {
  const stats = await client.getMemoryStats(params.namespace);
  return {
    total_memories: stats.count,
    storage_used: stats.size,
    topics: stats.top_topics,
    entities: stats.top_entities
  };
});
```

### Middleware Support

```javascript
// Add request middleware
client.use('request', (req, next) => {
  req.headers['X-Client-Version'] = '1.0.0';
  req.headers['X-Request-ID'] = generateRequestId();
  return next();
});

// Add response middleware
client.use('response', (res, next) => {
  console.log(`Response time: ${res.duration}ms`);
  return next();
});
```

### Batch Operations

```javascript
// Batch command processing
mcp.registerCommand('batch_store', async (params) => {
  const { memories } = params;
  
  const results = await client.batchCreate(memories, {
    chunkSize: 100,
    parallel: 4
  });
  
  return {
    created: results.success.length,
    failed: results.failed.length,
    errors: results.errors
  };
});
```

## Monitoring and Debugging

### Enable Debug Logging

```json
{
  "logging": {
    "level": "debug",
    "categories": {
      "auth": "debug",
      "connection": "info",
      "commands": "debug",
      "events": "trace"
    }
  }
}
```

### Health Check

```bash
# Check proxy status
unified-memory-mcp --health

# Output:
# MCP Proxy Status: Connected
# Server: http://10.10.20.100:9000
# Auth: Valid (expires in 3542s)
# Uptime: 2h 15m
# Commands processed: 1,247
# Events received: 3,891
```

### Diagnostic Commands

```bash
# Test connection
unified-memory-mcp --test-connection

# Validate configuration
unified-memory-mcp --validate-config

# Show current configuration (sanitized)
unified-memory-mcp --show-config

# Clear token cache
unified-memory-mcp --clear-cache
```

## Performance Optimization

### Connection Pooling

```json
{
  "performance": {
    "connectionPool": {
      "maxSockets": 10,
      "maxFreeSockets": 5,
      "timeout": 60000,
      "keepAlive": true
    }
  }
}
```

### Request Queuing

```json
{
  "performance": {
    "queue": {
      "concurrency": 5,
      "timeout": 30000,
      "retries": 3,
      "retryDelay": 1000
    }
  }
}
```

### Caching

```json
{
  "performance": {
    "cache": {
      "enabled": true,
      "ttl": 300,
      "maxSize": "50mb",
      "strategy": "lru"
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **Connection Failed**
   ```
   Error: ECONNREFUSED 10.10.20.100:9000
   ```
   - Verify server is running
   - Check firewall settings
   - Confirm network connectivity

2. **Authentication Error**
   ```
   Error: Invalid client credentials
   ```
   - Verify client ID and secret
   - Check token endpoint URL
   - Ensure credentials haven't expired

3. **Command Timeout**
   ```
   Error: Command timed out after 30000ms
   ```
   - Increase timeout in config
   - Check server performance
   - Verify network latency

### Debug Mode

Enable comprehensive debugging:

```bash
# Set debug environment
export DEBUG=unified-memory:*
export NODE_DEBUG=stream,http

# Run with verbose logging
unified-memory-mcp --verbose --log-http
```

### Log Analysis

```bash
# View recent errors
grep ERROR ~/.unified-memory/logs/mcp-proxy.log | tail -20

# Monitor real-time
tail -f ~/.unified-memory/logs/mcp-proxy.log | grep -E "ERROR|WARN"

# Analyze performance
grep "Response time" ~/.unified-memory/logs/mcp-proxy.log | \
  awk '{sum+=$4; count++} END {print "Avg:", sum/count, "ms"}'
```

## Security Considerations

### Token Storage

Tokens are stored securely using:
- Windows: Windows Credential Manager
- macOS: Keychain
- Linux: Secret Service API / libsecret

### Certificate Pinning

For production environments:

```json
{
  "security": {
    "pinning": {
      "enabled": true,
      "certificates": [
        "sha256//YourServerCertificateFingerprint"
      ]
    }
  }
}
```

### Audit Logging

```json
{
  "security": {
    "audit": {
      "enabled": true,
      "logFile": "~/.unified-memory/audit.log",
      "events": ["auth", "commands", "errors"]
    }
  }
}
```

## Upgrading

### Check for Updates

```bash
# Check current version
unified-memory-mcp --version

# Check for updates
npm outdated -g @unified-memory/mcp-proxy

# Update to latest
npm update -g @unified-memory/mcp-proxy
```

### Migration Guide

When upgrading from v1.x to v2.x:

1. Backup configuration
2. Update client binaries
3. Migrate config format
4. Test connection
5. Verify functionality

## API Reference

### Proxy Client API

```typescript
interface MCPProxyClient {
  // Lifecycle
  connect(): Promise<void>
  disconnect(): Promise<void>
  
  // Commands
  execute(command: string, params: any): Promise<any>
  registerCommand(name: string, handler: Function): void
  
  // Events
  on(event: string, handler: Function): void
  off(event: string, handler: Function): void
  
  // Health
  getStatus(): ProxyStatus
  getMetrics(): ProxyMetrics
}
```

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development setup and guidelines.

## Support

- GitHub Issues: https://github.com/eddygk/unified-memory-server/issues
- Documentation: https://docs.unified-memory.dev/mcp-proxy
- Community Forum: https://forum.unified-memory.dev