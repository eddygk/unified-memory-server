# 🎯 Unified Memory Server

A unified AI memory server integrating Neo4j, Basic Memory, and Redis Memory Server for multi-agent access. This project provides graph-based relationships, structured knowledge persistence, and conversational context with semantic search capabilities.

## 🎯 Overview

The Unified Memory Server combines three complementary memory systems to provide a complete memory solution for AI agents:

1. **Neo4j Memory System** - Graph-based relationship modeling and natural language querying
2. **Basic Memory (Obsidian)** - Structured knowledge with markdown persistence  
3. **Redis Memory Server** - Redis-powered memory system providing both short-term conversational context and long-term memory with semantic search capabilities

## 👥 Authors

- **Eddy Kawira** ([@eddygk](https://github.com/eddygk))
- **Claude AI** (Anthropic) - Architecture design and implementation guidance

## 🚀 Key Features

### Based on Redis Agent Memory Server

This project extends the [Redis Agent Memory Server](https://github.com/redis-developer/agent-memory-server) with:

- **Working Memory**: Session-scoped storage with automatic summarization
- **Long-Term Memory**: Persistent storage with semantic search capabilities
- **Graph Relationships**: Entity and relationship modeling with Neo4j
- **Structured Notes**: Markdown-based knowledge persistence with Basic Memory
- **Multi-Agent Support**: Namespace isolation for multiple AI agents
- **Authentication**: OAuth2/JWT support for secure multi-client access

### Additional Integrations

- **Neo4j Knowledge Graph**: Natural language queries and relationship traversal
- **Basic Memory (Obsidian)**: Persistent markdown notes and canvases
- **Cross-System Synchronization**: Unified access across all memory systems

## 📋 Prerequisites

- Docker Engine 24.0+
- Docker Compose 2.20+
- Git
- Python 3.12+ (for development)
- OpenSSL (for certificate generation)

## 🏃‍♂️ Quick Start

1. Clone the repository:
```bash
git clone https://github.com/eddygk/unified-memory-server.git
cd unified-memory-server
```

2. Copy environment template:
```bash
cp .env.example .env.production
```

3. Configure your environment variables (see Configuration section)

4. Start the services:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

5. Verify deployment:
```bash
curl http://localhost:8000/health
```

## 📚 Documentation

- [Deployment Guide](docs/deployment.md) - Complete deployment instructions for your subnet
- [Client Configuration](docs/client-config.md) - Setting up Claude and other AI agents
- [API Reference](docs/api.md) - REST API and MCP endpoints
- [Memory Selection Guide](docs/memory-selection.md) - When to use each memory system
- [Security Guide](docs/security.md) - Authentication and security best practices
- [MCP Proxy Client](docs/mcp-proxy.md) - OAuth2 proxy for Claude Desktop

## 🔧 Configuration

Key environment variables:

```bash
# Network Configuration
REDIS_URL=redis://redis:6379
PORT=8000
MCP_PORT=9000
HOST=0.0.0.0

# Authentication (Required for production)
DISABLE_AUTH=false
OAUTH2_ISSUER_URL=https://your-domain.auth0.com/
OAUTH2_AUDIENCE=https://memory.your-domain.local
OAUTH2_ALGORITHMS=["RS256"]

# AI Service Keys
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Memory Configuration
LONG_TERM_MEMORY=true
WINDOW_SIZE=20
ENABLE_TOPIC_EXTRACTION=true
ENABLE_NER=true

# Neo4j Configuration (optional)
NEO4J_URL=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password

# Basic Memory Configuration (optional)
BASIC_MEMORY_PATH=/path/to/obsidian/vault
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Agents (Clients)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Claude     │  │    GPT-4     │  │   Custom     │         │
│  │  (Windows)   │  │    (Mac)     │  │   Agents     │         │
│  └──────────┬───┘  └──────┬───────┘  └──────┬───────┘         │
└─────────────┼──────────────┼─────────────────┼─────────────────┘
              │              │                 │
              └──────────────┼─────────────────┘
                            │
         ┌──────────────────┴──────────────────┐
         │       Auth Proxy (OAuth2/JWT)       │
         └──────────────────┬──────────────────┘
                            │
    ┌───────────────────────┴───────────────────────────┐
    │              Unified Memory API                   │
    │    ┌────────────┐        ┌────────────┐          │
    │    │   REST     │        │    MCP     │          │
    │    │  :8000     │        │   :9000    │          │
    │    └────────────┘        └────────────┘          │
    └───────────────────────┬───────────────────────────┘
                            │
        ┌───────────────────┴───────────────────────┐
        │        Memory System Selector             │
        └───────┬───────────────┬───────────────┬───┘
                │               │               │
    ┌───────────▼──────┐ ┌─────▼──────────┐ ┌──▼────────┐
    │     Neo4j       │ │ Basic Memory   │ │  Redis    │
    │  (Graph DB)     │ │  (Markdown)    │ │ (Cache)   │
    └─────────────────┘ └────────────────┘ └───────────┘
```

## 🌐 Network Deployment (10.10.20.0/24)

This server is designed to run on a dedicated machine in your subnet:

- **Server**: 10.10.20.100 (example)
- **API Port**: 8000
- **MCP Port**: 9000
- **Monitoring**: Grafana on port 3000

See [deployment guide](docs/deployment.md) for detailed subnet setup.

## 🔌 Client Integration

### Claude Desktop (Windows/Mac)
```json
{
  "mcpServers": {
    "unified-memory": {
      "command": "node",
      "args": ["/path/to/memory-client/index.js"],
      "env": {
        "MEMORY_SERVER_URL": "http://memory.local:9000/sse",
        "AUTH0_CLIENT_ID": "your-client-id",
        "AUTH0_CLIENT_SECRET": "your-secret",
        "NAMESPACE": "claude"
      }
    }
  }
}
```

### Python Client
```python
from unified_memory_client import MemoryClient

client = MemoryClient(
    base_url="http://memory.local:8000",
    client_id="your-client-id",
    client_secret="your-secret"
)

# Store memory
client.create_memory("Important information", topics=["topic1"])

# Search memories
results = client.search("query text", limit=5)
```

## 🧪 Testing

```bash
# Run tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Manual testing
python tests/test_auth.py
python tests/test_memory_operations.py
```

## 📊 Monitoring

- Grafana Dashboard: http://localhost:3000
- Prometheus Metrics: http://localhost:9090
- Redis Insight: http://localhost:18001

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Redis Agent Memory Server](https://github.com/redis-developer/agent-memory-server) - Core Redis memory implementation
- [Neo4j](https://neo4j.com/) - Graph database for relationship modeling
- [Basic Memory](https://github.com/BasicMemory/basic-memory) - Markdown-based knowledge persistence
- [Anthropic](https://www.anthropic.com/) - Claude AI assistance in architecture and implementation

## 📞 Support

- Issues: [GitHub Issues](https://github.com/eddygk/unified-memory-server/issues)
- Discussions: [GitHub Discussions](https://github.com/eddygk/unified-memory-server/discussions)

---

*Built with ❤️ by Eddy Kawira and Claude AI*