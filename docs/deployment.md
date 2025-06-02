# Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Unified Memory Server in your 10.10.20.0/24 subnet environment. The deployment uses Docker Compose for orchestration and includes all three memory systems: Neo4j, Basic Memory, and Redis Memory Server.

## Prerequisites

### System Requirements
- **OS**: Ubuntu 22.04 LTS or later (recommended) / Windows Server 2022 / macOS 12+
- **CPU**: 4 cores minimum, 8 cores recommended
- **RAM**: 16GB minimum, 32GB recommended
- **Storage**: 100GB SSD minimum, 500GB recommended
- **Network**: Static IP in 10.10.20.0/24 subnet

### Software Requirements
- Docker Engine 24.0+
- Docker Compose 2.20+
- Git
- Python 3.12+ (for management scripts)
- OpenSSL (for certificate generation)

### Network Requirements
- Available IP address in 10.10.20.0/24 range
- Firewall rules allowing:
  - Port 8000 (REST API)
  - Port 9000 (MCP Protocol)
  - Port 3000 (Grafana monitoring)
  - Port 7474 (Neo4j Browser - optional)
  - Port 6379 (Redis - internal only)

## Network Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   10.10.20.0/24 Subnet                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐         ┌─────────────────┐          │
│  │ Memory Server   │         │ Client Devices  │          │
│  │ 10.10.20.100   │◄────────┤ 10.10.20.x     │          │
│  │ Ports:         │         │ - Windows PCs   │          │
│  │ - 8000 (API)   │         │ - Mac devices   │          │
│  │ - 9000 (MCP)   │         │ - Linux nodes   │          │
│  │ - 3000 (Mon)   │         └─────────────────┘          │
│  └─────────────────┘                                       │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                       │
│  │ Firewall Rules  │                                       │
│  │ - Allow 8000    │                                       │
│  │ - Allow 9000    │                                       │
│  │ - Allow 3000    │                                       │
│  └─────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
```

## Step-by-Step Deployment

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
```

### 2. Clone Repository

```bash
# Create deployment directory
sudo mkdir -p /opt/unified-memory
cd /opt/unified-memory

# Clone repository
git clone https://github.com/eddygk/unified-memory-server.git
cd unified-memory-server

# Set permissions
sudo chown -R $USER:$USER /opt/unified-memory
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env.production

# Generate secure passwords
echo "Generating secure passwords..."
NEO4J_PASS=$(openssl rand -base64 32)
REDIS_PASS=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -base64 64)

# Update .env.production
cat > .env.production << EOF
# Network Configuration
REDIS_URL=redis://default:${REDIS_PASS}@redis:6379
PORT=8000
MCP_PORT=9000
HOST=0.0.0.0
SERVER_IP=10.10.20.100

# Authentication
DISABLE_AUTH=false
OAUTH2_ISSUER_URL=https://your-domain.auth0.com/
OAUTH2_AUDIENCE=https://memory.your-domain.local
OAUTH2_ALGORITHMS=["RS256"]
JWT_SECRET=${JWT_SECRET}

# AI Service Keys
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Memory Configuration
LONG_TERM_MEMORY=true
WINDOW_SIZE=20
ENABLE_TOPIC_EXTRACTION=true
ENABLE_NER=true

# Neo4j Configuration
NEO4J_URL=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=${NEO4J_PASS}

# Basic Memory Configuration
BASIC_MEMORY_PATH=/data/obsidian
BASIC_MEMORY_SYNC=true

# Redis Configuration
REDIS_PASSWORD=${REDIS_PASS}
REDIS_MAX_MEMORY=4gb

# Monitoring
ENABLE_MONITORING=true
GRAFANA_ADMIN_PASSWORD=changeme
EOF
```

### 4. Configure OAuth2 Provider

#### Option A: Auth0 Setup
1. Create new Auth0 application
2. Set callback URLs: `http://10.10.20.100:8000/callback`
3. Enable Client Credentials grant
4. Note Client ID and Secret

#### Option B: AWS Cognito Setup
1. Create User Pool
2. Create App Client with client credentials flow
3. Note Pool ID and Client details

Update `.env.production` with your OAuth2 details.

### 5. Prepare Data Directories

```bash
# Create persistent storage directories
sudo mkdir -p /data/unified-memory/{neo4j,redis,obsidian,grafana}
sudo mkdir -p /data/unified-memory/backups

# Set permissions
sudo chown -R 1000:1000 /data/unified-memory
```

### 6. Deploy Services

```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Start services in detached mode
docker-compose -f docker-compose.prod.yml up -d

# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 7. Verify Deployment

```bash
# Check API health
curl http://10.10.20.100:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "services": {
#     "redis": "connected",
#     "neo4j": "connected",
#     "basic_memory": "connected"
#   }
# }

# Test authentication
curl -X POST http://10.10.20.100:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"client_id": "your-client-id", "client_secret": "your-secret"}'

# Access monitoring
# Open browser to http://10.10.20.100:3000
# Login: admin / changeme (update immediately)
```

### 8. Configure Firewall

```bash
# UFW example (Ubuntu)
sudo ufw allow from 10.10.20.0/24 to any port 8000
sudo ufw allow from 10.10.20.0/24 to any port 9000
sudo ufw allow from 10.10.20.0/24 to any port 3000
sudo ufw reload

# Windows Firewall (PowerShell as Admin)
New-NetFirewallRule -DisplayName "Memory API" -Direction Inbound -Protocol TCP -LocalPort 8000 -RemoteAddress 10.10.20.0/24 -Action Allow
New-NetFirewallRule -DisplayName "Memory MCP" -Direction Inbound -Protocol TCP -LocalPort 9000 -RemoteAddress 10.10.20.0/24 -Action Allow
New-NetFirewallRule -DisplayName "Memory Monitor" -Direction Inbound -Protocol TCP -LocalPort 3000 -RemoteAddress 10.10.20.0/24 -Action Allow
```

## Production Considerations

### SSL/TLS Configuration

For production, enable HTTPS:

```bash
# Generate self-signed certificate (for internal use)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /data/unified-memory/certs/server.key \
  -out /data/unified-memory/certs/server.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=memory.local"

# Update docker-compose.prod.yml to mount certificates
# Add to api service:
volumes:
  - /data/unified-memory/certs:/certs:ro
environment:
  - SSL_CERT=/certs/server.crt
  - SSL_KEY=/certs/server.key
```

### Backup Strategy

```bash
# Create backup script
cat > /opt/unified-memory/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/data/unified-memory/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup Neo4j
docker exec neo4j neo4j-admin dump --to=/backups/neo4j-backup.dump
cp /data/unified-memory/neo4j/backups/neo4j-backup.dump $BACKUP_DIR/

# Backup Redis
docker exec redis redis-cli --rdb /data/dump.rdb
cp /data/unified-memory/redis/dump.rdb $BACKUP_DIR/

# Backup Obsidian vault
tar -czf $BACKUP_DIR/obsidian-backup.tar.gz /data/unified-memory/obsidian

echo "Backup completed: $BACKUP_DIR"
EOF

chmod +x /opt/unified-memory/backup.sh

# Add to crontab for daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/unified-memory/backup.sh") | crontab -
```

### Monitoring Setup

1. Access Grafana at http://10.10.20.100:3000
2. Import provided dashboards from `monitoring/dashboards/`
3. Configure alerts for:
   - High memory usage (>80%)
   - Service disconnections
   - API response time (>1s)
   - Error rate (>5%)

### Performance Tuning

```bash
# Neo4j tuning (neo4j.conf)
dbms.memory.heap.initial_size=2g
dbms.memory.heap.max_size=4g
dbms.memory.pagecache.size=2g

# Redis tuning (redis.conf)
maxmemory 4gb
maxmemory-policy allkeys-lru

# System tuning
echo "vm.overcommit_memory = 1" >> /etc/sysctl.conf
echo "net.core.somaxconn = 65535" >> /etc/sysctl.conf
sysctl -p
```

## Troubleshooting

### Common Issues

1. **Services won't start**
   ```bash
   # Check logs
   docker-compose -f docker-compose.prod.yml logs [service-name]
   
   # Verify ports aren't in use
   sudo netstat -tlnp | grep -E "8000|9000|3000"
   ```

2. **Authentication failures**
   ```bash
   # Verify OAuth2 configuration
   curl -X GET https://your-domain.auth0.com/.well-known/openid-configuration
   
   # Check JWT token
   docker exec unified-memory-api python -m scripts.verify_auth
   ```

3. **Memory issues**
   ```bash
   # Check Docker resource limits
   docker stats
   
   # Increase limits in docker-compose.prod.yml
   ```

### Health Checks

```bash
# Create health check script
cat > /opt/unified-memory/health-check.sh << 'EOF'
#!/bin/bash
SERVICES=("redis" "neo4j" "api" "mcp-proxy")
for service in "${SERVICES[@]}"; do
    if docker-compose -f docker-compose.prod.yml ps | grep -q "$service.*Up"; then
        echo "✓ $service is healthy"
    else
        echo "✗ $service is down"
        # Attempt restart
        docker-compose -f docker-compose.prod.yml restart $service
    fi
done
EOF

chmod +x /opt/unified-memory/health-check.sh
```

## Client Configuration

See [Client Configuration Guide](client-config.md) for detailed instructions on setting up:
- Claude Desktop (Windows/Mac)
- Python clients
- JavaScript/TypeScript clients
- MCP proxy configuration

## Maintenance

### Regular Tasks
- Monitor disk usage: `df -h /data/unified-memory`
- Check logs: `docker-compose -f docker-compose.prod.yml logs --tail=100`
- Update images: `docker-compose -f docker-compose.prod.yml pull`
- Rotate logs: Configure logrotate for Docker logs

### Updates
```bash
# Backup before updating
/opt/unified-memory/backup.sh

# Pull latest changes
cd /opt/unified-memory/unified-memory-server
git pull origin main

# Update services
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## Security Checklist

- [ ] Change all default passwords
- [ ] Configure firewall rules
- [ ] Enable SSL/TLS
- [ ] Set up OAuth2 authentication
- [ ] Configure backup encryption
- [ ] Enable audit logging
- [ ] Restrict file permissions
- [ ] Set up intrusion detection
- [ ] Configure rate limiting
- [ ] Enable CORS appropriately

## Support

For issues or questions:
- Check logs: `docker-compose logs [service]`
- GitHub Issues: https://github.com/eddygk/unified-memory-server/issues
- Documentation: https://github.com/eddygk/unified-memory-server/docs