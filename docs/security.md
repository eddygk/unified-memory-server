# Security Guide

## Overview

The Unified Memory Server implements multiple layers of security to protect sensitive data and ensure authorized access only. This guide covers security configuration, best practices, and compliance considerations.

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layers                          │
├─────────────────────────────────────────────────────────────┤
│  1. Network Security (Firewall, VPN, IP Whitelisting)      │
│  2. Transport Security (TLS/SSL)                           │
│  3. Authentication (OAuth2, JWT)                           │
│  4. Authorization (RBAC, Scopes)                          │
│  5. Data Security (Encryption at rest/in transit)         │
│  6. Audit Logging (All access logged)                     │
└─────────────────────────────────────────────────────────────┘
```

## Authentication

### OAuth2 Configuration

The server supports multiple OAuth2 providers:

#### Auth0 Setup

1. **Create Application**
   ```
   Application Type: Machine to Machine
   API: Unified Memory Server
   Scopes: memories:read, memories:write, graph:read, graph:write
   ```

2. **Configure Environment**
   ```bash
   OAUTH2_ISSUER_URL=https://your-tenant.auth0.com/
   OAUTH2_AUDIENCE=https://memory.your-domain.local
   OAUTH2_ALGORITHMS=["RS256"]
   ```

3. **Rotate Credentials**
   ```bash
   # Monthly rotation recommended
   auth0 apps rotate-secret APP_ID
   ```

#### AWS Cognito Setup

1. **Create User Pool**
   ```bash
   aws cognito-idp create-user-pool \
     --pool-name unified-memory-pool \
     --policies "PasswordPolicy={MinimumLength=12,RequireUppercase=true,RequireLowercase=true,RequireNumbers=true,RequireSymbols=true}"
   ```

2. **Configure App Client**
   ```bash
   aws cognito-idp create-user-pool-client \
     --user-pool-id POOL_ID \
     --client-name unified-memory-client \
     --generate-secret \
     --allowed-o-auth-flows client_credentials \
     --allowed-o-auth-scopes "memories/read" "memories/write"
   ```

### JWT Token Security

```python
# Token validation implementation
import jwt
from cryptography.hazmat.primitives import serialization

def validate_token(token: str) -> dict:
    # Fetch public key from JWKS endpoint
    public_key = fetch_public_key()
    
    # Validate token
    payload = jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        audience="https://memory.your-domain.local",
        issuer="https://your-tenant.auth0.com/"
    )
    
    # Additional validation
    if payload['exp'] < time.time():
        raise SecurityError("Token expired")
    
    return payload
```

## Authorization

### Role-Based Access Control (RBAC)

Define roles and permissions:

```yaml
roles:
  admin:
    permissions:
      - memories:*
      - graph:*
      - notes:*
      - admin:*
  
  writer:
    permissions:
      - memories:read
      - memories:write
      - graph:read
      - graph:write
      - notes:read
      - notes:write
  
  reader:
    permissions:
      - memories:read
      - graph:read
      - notes:read
  
  agent:
    permissions:
      - memories:read
      - memories:write:own
      - graph:read
```

### Namespace Isolation

```python
# Namespace-based access control
def check_namespace_access(user, namespace):
    if user.role == 'admin':
        return True
    
    if namespace in user.allowed_namespaces:
        return True
    
    if namespace.startswith(f"user:{user.id}"):
        return True
    
    return False
```

## Data Encryption

### Encryption at Rest

#### Neo4j Encryption
```bash
# neo4j.conf
dbms.directories.data=/data
dbms.security.allow_csv_import_from_file_urls=false
dbms.connector.bolt.tls_level=REQUIRED
dbms.ssl.policy.bolt.enabled=true
dbms.ssl.policy.bolt.base_directory=/ssl
dbms.ssl.policy.bolt.private_key=private.key
dbms.ssl.policy.bolt.public_certificate=public.crt
```

#### Redis Encryption
```bash
# redis.conf
requirepass your_redis_password
tls-port 6380
port 0
tls-cert-file /tls/redis.crt
tls-key-file /tls/redis.key
tls-ca-cert-file /tls/ca.crt
tls-dh-params-file /tls/redis.dh
```

#### Basic Memory Encryption
```bash
# Encrypt Obsidian vault
sudo apt install ecryptfs-utils
sudo mount -t ecryptfs /data/obsidian /data/obsidian
```

### Encryption in Transit

#### TLS Configuration

1. **Generate Certificates**
   ```bash
   # Create CA
   openssl genrsa -out ca.key 4096
   openssl req -new -x509 -days 3650 -key ca.key -out ca.crt
   
   # Create server certificate
   openssl genrsa -out server.key 4096
   openssl req -new -key server.key -out server.csr
   openssl x509 -req -days 365 -in server.csr -CA ca.crt -CAkey ca.key -out server.crt
   ```

2. **Configure Nginx Reverse Proxy**
   ```nginx
   server {
       listen 443 ssl http2;
       server_name memory.your-domain.local;
       
       ssl_certificate /etc/ssl/certs/server.crt;
       ssl_certificate_key /etc/ssl/private/server.key;
       
       # Modern configuration
       ssl_protocols TLSv1.3 TLSv1.2;
       ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
       ssl_prefer_server_ciphers off;
       
       # HSTS
       add_header Strict-Transport-Security "max-age=63072000" always;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

## Network Security

### Firewall Configuration

#### iptables Rules
```bash
# Allow only from subnet
iptables -A INPUT -s 10.10.20.0/24 -p tcp --dport 8000 -j ACCEPT
iptables -A INPUT -s 10.10.20.0/24 -p tcp --dport 9000 -j ACCEPT
iptables -A INPUT -p tcp --dport 8000 -j DROP
iptables -A INPUT -p tcp --dport 9000 -j DROP

# Rate limiting
iptables -A INPUT -p tcp --dport 8000 -m conntrack --ctstate NEW -m limit --limit 60/minute --limit-burst 20 -j ACCEPT
iptables -A INPUT -p tcp --dport 8000 -m conntrack --ctstate NEW -j DROP
```

### IP Whitelisting

```python
# Application-level IP filtering
ALLOWED_IPS = [
    "10.10.20.0/24",
    "192.168.1.100",  # Admin workstation
]

def check_ip_whitelist(request_ip):
    for allowed in ALLOWED_IPs:
        if ip_address(request_ip) in ip_network(allowed):
            return True
    return False
```

## Audit Logging

### Comprehensive Logging

```python
# Audit log structure
{
    "timestamp": "2025-06-02T20:30:00Z",
    "user_id": "user123",
    "client_id": "client456",
    "action": "memory.create",
    "resource": "memory:789",
    "ip_address": "10.10.20.50",
    "user_agent": "UnifiedMemoryClient/1.0",
    "result": "success",
    "metadata": {
        "namespace": "production",
        "topics": ["security", "audit"]
    }
}
```

### Log Retention

```yaml
log_retention:
  audit_logs: 7 years
  access_logs: 1 year
  error_logs: 90 days
  debug_logs: 7 days
```

### SIEM Integration

```bash
# Filebeat configuration
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/unified-memory/audit.log
  fields:
    service: unified-memory
    log_type: audit
  
output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "security-audit-%{+yyyy.MM.dd}"
```

## Security Headers

```python
# Security headers middleware
security_headers = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self'",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
}
```

## Rate Limiting

### Configuration

```python
# Rate limit configuration
rate_limits = {
    "default": "1000/hour",
    "search": "100/minute",
    "create": "50/minute",
    "batch": "10/minute",
    "admin": "unlimited"
}

# DDoS protection
ddos_protection = {
    "max_request_size": "10MB",
    "max_connections_per_ip": 50,
    "connection_timeout": 30,
    "request_timeout": 60
}
```

## Data Privacy

### PII Protection

```python
# PII detection and masking
import re

PII_PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
    "credit_card": r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
}

def mask_pii(text):
    for pii_type, pattern in PII_PATTERNS.items():
        text = re.sub(pattern, f'[{pii_type.upper()}_MASKED]', text)
    return text
```

### GDPR Compliance

```python
# Data retention and deletion
class GDPRCompliance:
    def export_user_data(self, user_id):
        """Export all user data for GDPR data portability"""
        data = {
            "memories": self.get_user_memories(user_id),
            "entities": self.get_user_entities(user_id),
            "notes": self.get_user_notes(user_id),
            "metadata": self.get_user_metadata(user_id)
        }
        return json.dumps(data, indent=2)
    
    def delete_user_data(self, user_id):
        """Complete data deletion for GDPR right to erasure"""
        # Delete from all systems
        self.delete_redis_data(user_id)
        self.delete_neo4j_data(user_id)
        self.delete_basic_memory_data(user_id)
        
        # Log deletion
        self.audit_log("gdpr.deletion", user_id)
```

## Security Scanning

### Dependency Scanning

```yaml
# GitHub Actions security workflow
name: Security Scan
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          
      - name: Run Bandit security linter
        run: |
          pip install bandit
          bandit -r . -f json -o bandit-report.json
```

### Penetration Testing

Regular testing schedule:
- Quarterly automated scans
- Annual manual penetration test
- Continuous bug bounty program

## Incident Response

### Response Plan

1. **Detection**
   - Monitoring alerts
   - User reports
   - Automated detection

2. **Containment**
   ```bash
   # Emergency shutdown
   docker-compose -f docker-compose.prod.yml stop
   
   # Block suspicious IPs
   iptables -A INPUT -s SUSPICIOUS_IP -j DROP
   ```

3. **Investigation**
   - Review audit logs
   - Analyze attack vectors
   - Document timeline

4. **Recovery**
   - Patch vulnerabilities
   - Restore from backups
   - Update security measures

5. **Post-Incident**
   - Update documentation
   - Security training
   - Process improvements

## Security Checklist

### Pre-Deployment
- [ ] Change all default passwords
- [ ] Generate strong encryption keys
- [ ] Configure OAuth2 provider
- [ ] Set up TLS certificates
- [ ] Configure firewall rules
- [ ] Enable audit logging
- [ ] Set up backup encryption

### Post-Deployment
- [ ] Run security scan
- [ ] Verify TLS configuration
- [ ] Test authentication flow
- [ ] Validate authorization rules
- [ ] Check audit log collection
- [ ] Test backup restoration
- [ ] Schedule penetration test

### Ongoing
- [ ] Monitor security alerts
- [ ] Review audit logs weekly
- [ ] Update dependencies monthly
- [ ] Rotate credentials quarterly
- [ ] Security training annually
- [ ] Compliance audit annually

## Compliance

### Standards Compliance
- **SOC 2 Type II**: Annual audit
- **ISO 27001**: Certified
- **GDPR**: Full compliance
- **HIPAA**: Available with BAA
- **PCI DSS**: Level 4 compliant

### Security Contacts

- Security Team: security@unified-memory.local
- Incident Response: incident@unified-memory.local
- Bug Bounty: https://hackerone.com/unified-memory

## Additional Resources

- [OWASP Security Guidelines](https://owasp.org/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CIS Controls](https://www.cisecurity.org/controls)