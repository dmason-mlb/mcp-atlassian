# MCP Server Deployment and Configuration Guide

**Created:** July 29, 2025
**Version:** 1.0.0
**Purpose:** Comprehensive deployment and configuration guide for the MCP Atlassian server

## Overview

This guide provides complete instructions for deploying and configuring the MCP Atlassian server across different environments and MCP clients. The server provides AI assistants with access to Jira and Confluence through the Model Context Protocol (MCP).

## Quick Start

### Prerequisites

- Python 3.9 or higher
- `uv` package manager (recommended) or `pip`
- Access to Jira and/or Confluence instances
- Valid authentication credentials (API tokens, OAuth, or PAT)

### Installation

```bash
# Clone the repository
git clone https://github.com/dmason-mlb/mcp-atlassian.git
cd mcp-atlassian

# Install dependencies
uv sync --frozen --all-extras --dev

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate.ps1  # Windows
```

### Basic Configuration

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Configure authentication (choose one method):**

   **API Token (Cloud - Recommended):**
   ```bash
   ATLASSIAN_URL=https://your-domain.atlassian.net
   ATLASSIAN_EMAIL=your-email@company.com
   ATLASSIAN_API_TOKEN=your-api-token
   ```

   **OAuth 2.0 (Cloud - Advanced):**
   ```bash
   ATLASSIAN_URL=https://your-domain.atlassian.net
   ATLASSIAN_OAUTH_CLIENT_ID=your-client-id
   ATLASSIAN_OAUTH_CLIENT_SECRET=your-client-secret
   ATLASSIAN_OAUTH_REDIRECT_URI=http://localhost:8000/callback
   ```

   **Personal Access Token (Server/DC):**
   ```bash
   JIRA_URL=https://jira.your-company.com
   CONFLUENCE_URL=https://confluence.your-company.com
   ATLASSIAN_PAT=your-personal-access-token
   ```

3. **Test configuration:**
   ```bash
   uv run mcp-atlassian --env-file .env -v
   ```

## Authentication Methods

### 1. API Token Authentication (Cloud)

**Best for:** Individual users, development, and small teams

**Setup Steps:**
1. Log in to your Atlassian account
2. Go to [Account Settings → Security → API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
3. Create a new API token
4. Configure environment:

```bash
# .env file
ATLASSIAN_URL=https://mycompany.atlassian.net
ATLASSIAN_EMAIL=john.doe@company.com
ATLASSIAN_API_TOKEN=ATATT3xFfGF0abcd1234efgh5678ijklmnopqrstuvwxyz

# Optional: Restrict to specific projects/spaces
JIRA_PROJECTS_FILTER=PROJ,DEV,SUPPORT
CONFLUENCE_SPACES_FILTER=DEV,DOCS,TEAM
```

### 2. OAuth 2.0 Authentication (Cloud)

**Best for:** Production deployments, multi-user environments, and enterprise

**Prerequisites:**
- Atlassian OAuth 2.0 app registration
- Client ID and client secret

**Setup Steps:**

1. **Register OAuth App:**
   - Go to [Atlassian Developer Console](https://developer.atlassian.com/console/myapps/)
   - Create new app → OAuth 2.0 (3LO)
   - Add required scopes:
     - `read:jira-work`
     - `write:jira-work`
     - `read:confluence-content.all`
     - `write:confluence-content`

2. **Configure OAuth:**
   ```bash
   # .env file
   ATLASSIAN_URL=https://mycompany.atlassian.net
   ATLASSIAN_OAUTH_CLIENT_ID=your-oauth-client-id
   ATLASSIAN_OAUTH_CLIENT_SECRET=your-oauth-client-secret
   ATLASSIAN_OAUTH_REDIRECT_URI=http://localhost:8000/callback
   ```

3. **Run OAuth Setup Wizard:**
   ```bash
   uv run mcp-atlassian --oauth-setup -v
   ```

4. **Follow browser prompts to complete authorization**

### 3. Personal Access Token (Server/DC)

**Best for:** Atlassian Server and Data Center instances

**Setup Steps:**
1. Log in to your Atlassian instance
2. Go to Profile → Personal Access Tokens
3. Create token with appropriate permissions
4. Configure environment:

```bash
# .env file
JIRA_URL=https://jira.mycompany.com
CONFLUENCE_URL=https://confluence.mycompany.com
ATLASSIAN_PAT=your-personal-access-token

# Optional: Disable SSL verification for internal instances
ATLASSIAN_SSL_VERIFY=false
```

### 4. Multi-User HTTP Authentication

**Best for:** Multi-tenant deployments, shared services

**Configuration:**
```bash
# .env file
MCP_TRANSPORT=sse  # or streamable-http
MCP_PORT=9000
ATLASSIAN_MULTI_USER=true

# Optional: Default instance URLs
JIRA_URL=https://default.atlassian.net
CONFLUENCE_URL=https://default.atlassian.net/wiki
```

**Usage with headers:**
```bash
curl -H "X-Atlassian-Token: user-api-token" \
     -H "X-Atlassian-Email: user@company.com" \
     http://localhost:9000/mcp/call
```

## MCP Client Configuration

### Claude Code (Official Anthropic CLI)

**Installation:**
```bash
# Install Claude Code
npm install -g @anthropic-ai/claude-code

# OR using official installer
curl -sSL https://install.claudecode.com | bash
```

**Configuration:**

1. **Create MCP configuration file:**
   ```bash
   # Create directory
   mkdir -p ~/.claude/mcp

   # Create config file
   cat > ~/.claude/mcp/config.json << 'EOF'
   {
     "servers": {
       "atlassian": {
         "command": "uv",
         "args": ["run", "mcp-atlassian"],
         "cwd": "/path/to/mcp-atlassian",
         "env": {
           "ATLASSIAN_URL": "https://your-domain.atlassian.net",
           "ATLASSIAN_EMAIL": "your-email@company.com",
           "ATLASSIAN_API_TOKEN": "your-api-token"
         }
       }
     }
   }
   EOF
   ```

2. **Alternative: Use environment file:**
   ```json
   {
     "servers": {
       "atlassian": {
         "command": "uv",
         "args": ["run", "mcp-atlassian", "--env-file", "/path/to/.env"],
         "cwd": "/path/to/mcp-atlassian"
       }
     }
   }
   ```

3. **Test connection:**
   ```bash
   claude-code list-servers
   claude-code test-server atlassian
   ```

4. **Start Claude Code with MCP:**
   ```bash
   claude-code --mcp
   ```

### Cursor IDE

**Configuration:**

1. **Open Cursor settings** (`Cmd/Ctrl + ,`)

2. **Add MCP server configuration:**
   - Go to Extensions → MCP
   - Add new server:
     ```json
     {
       "name": "Atlassian",
       "command": "uv",
       "args": ["run", "mcp-atlassian"],
       "cwd": "/path/to/mcp-atlassian",
       "env": {
         "ATLASSIAN_EMAIL": "your-email@company.com",
         "ATLASSIAN_API_TOKEN": "your-api-token",
         "JIRA_URL": "https://your-domain.atlassian.net",
         "CONFLUENCE_URL": "https://your-domain.atlassian.net/wiki"
       }
     }
     ```

3. **Alternative: Cursor MCP config file:**
   ```bash
   # Create Cursor MCP config
   mkdir -p ~/.cursor/mcp
   cat > ~/.cursor/mcp/config.json << 'EOF'
   {
     "servers": {
       "atlassian": {
         "command": "uv",
         "args": ["run", "mcp-atlassian", "--env-file", "/path/to/.env"],
         "cwd": "/path/to/mcp-atlassian"
       }
     }
   }
   EOF
   ```

4. **Restart Cursor** and verify MCP connection in status bar

### Claude Desktop (Anthropic)

**Configuration:**

1. **Locate Claude Desktop config directory:**
   - **macOS:** `~/Library/Application Support/Claude/`
   - **Windows:** `%APPDATA%\Claude\`
   - **Linux:** `~/.config/Claude/`

2. **Create or edit `claude_desktop_config.json`:**
   ```json
   {
     "mcpServers": {
       "atlassian": {
         "command": "uv",
         "args": ["run", "mcp-atlassian"],
         "cwd": "/path/to/mcp-atlassian",
         "env": {
           "ATLASSIAN_URL": "https://your-domain.atlassian.net",
           "ATLASSIAN_EMAIL": "your-email@company.com",
           "ATLASSIAN_API_TOKEN": "your-api-token"
         }
       }
     }
   }
   ```

3. **Alternative: Use environment file:**
   ```json
   {
     "mcpServers": {
       "atlassian": {
         "command": "uv",
         "args": ["run", "mcp-atlassian", "--env-file", "/path/to/.env"],
         "cwd": "/path/to/mcp-atlassian"
       }
     }
   }
   ```

4. **Restart Claude Desktop**

### VS Code with MCP Extension

**Installation:**
1. Install the MCP extension from VS Code marketplace
2. Open VS Code settings (`Cmd/Ctrl + ,`)

**Configuration:**
```json
{
  "mcp.servers": {
    "atlassian": {
      "command": "uv",
      "args": ["run", "mcp-atlassian"],
      "cwd": "/path/to/mcp-atlassian",
      "env": {
        "ATLASSIAN_URL": "https://your-domain.atlassian.net",
        "ATLASSIAN_EMAIL": "your-email@company.com",
        "ATLASSIAN_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

### Generic MCP Client

**For any MCP-compatible client:**

1. **STDIO Transport (Default):**
   ```bash
   # Start server
   uv run mcp-atlassian --env-file .env
   ```

2. **HTTP Transport (SSE):**
   ```bash
   # Start HTTP server
   uv run mcp-atlassian --transport sse --port 9000 --env-file .env

   # Connect via HTTP
   curl -N -H "Accept: text/event-stream" \
        http://localhost:9000/sse
   ```

3. **HTTP Transport (Streamable):**
   ```bash
   # Start streamable HTTP server
   uv run mcp-atlassian --transport streamable-http --port 9000 --env-file .env

   # Connect via WebSocket or HTTP
   wscat -c ws://localhost:9000/ws
   ```

## Advanced Configuration

### Environment Variables Reference

#### Core Configuration
```bash
# Transport and server settings
MCP_TRANSPORT=stdio|sse|streamable-http  # Default: stdio
MCP_PORT=9000                            # HTTP transport port
MCP_HOST=localhost                       # HTTP transport host

# Logging
LOG_LEVEL=INFO|DEBUG|WARNING|ERROR       # Default: INFO
ATLASSIAN_LOG_LEVEL=INFO                 # Atlassian-specific logging

# Performance and reliability
ATLASSIAN_TIMEOUT=30                     # Request timeout in seconds
ATLASSIAN_MAX_RETRIES=3                  # Maximum retry attempts
ATLASSIAN_RETRY_DELAY=1                  # Delay between retries (seconds)
```

#### Authentication Settings
```bash
# API Token authentication
ATLASSIAN_EMAIL=user@company.com
ATLASSIAN_API_TOKEN=your-api-token

# OAuth 2.0 authentication
ATLASSIAN_OAUTH_CLIENT_ID=your-client-id
ATLASSIAN_OAUTH_CLIENT_SECRET=your-client-secret
ATLASSIAN_OAUTH_REDIRECT_URI=http://localhost:8000/callback

# Personal Access Token (Server/DC)
ATLASSIAN_PAT=your-personal-access-token

# Multi-user mode
ATLASSIAN_MULTI_USER=true|false          # Default: false
```

#### Service URLs
```bash
# Instance URLs
ATLASSIAN_URL=https://company.atlassian.net
# Alternative: Set individually for Server/DC
# JIRA_URL=https://company.atlassian.net
# CONFLUENCE_URL=https://company.atlassian.net/wiki

# Server/DC URLs
JIRA_URL=https://jira.company.com
CONFLUENCE_URL=https://confluence.company.com
```

#### Security and SSL
```bash
# SSL verification
ATLASSIAN_VERIFY_SSL=true|false          # Default: true
ATLASSIAN_CA_BUNDLE=/path/to/ca-bundle.pem

# Proxy settings
ATLASSIAN_PROXY_HTTP=http://proxy:8080
ATLASSIAN_PROXY_HTTPS=https://proxy:8080
ATLASSIAN_NO_PROXY=localhost,127.0.0.1,.company.com
```

#### Content Filtering
```bash
# Restrict to specific projects/spaces
JIRA_PROJECTS_FILTER=PROJ,DEV,TEST      # Comma-separated project keys
CONFLUENCE_SPACES_FILTER=DEV,DOCS       # Comma-separated space keys

# Tool enablement
ATLASSIAN_ENABLE_JIRA=true|false         # Default: true
ATLASSIAN_ENABLE_CONFLUENCE=true|false   # Default: true
ATLASSIAN_READ_ONLY=true|false           # Default: false
```

#### ADF and Formatting
```bash
# ADF (Atlassian Document Format) settings
ATLASSIAN_ENABLE_ADF=true|false          # Default: true (Cloud instances)
ATLASSIAN_FORCE_WIKI_MARKUP=true|false  # Force wiki markup format
ATLASSIAN_DISABLE_ADF=true|false         # Disable ADF globally
```

### HTTP Transport Configuration

**Server-Sent Events (SSE):**
```bash
# Start SSE server
uv run mcp-atlassian --transport sse --port 9000 --host 0.0.0.0

# Client connection
curl -N -H "Accept: text/event-stream" \
     -H "X-Atlassian-Token: your-token" \
     -H "X-Atlassian-Email: your-email" \
     http://localhost:9000/sse
```

**Streamable HTTP:**
```bash
# Start streamable server
uv run mcp-atlassian --transport streamable-http --port 9000

# WebSocket connection
wscat -c ws://localhost:9000/ws

# HTTP POST requests
curl -X POST http://localhost:9000/mcp \
     -H "Content-Type: application/json" \
     -H "X-Atlassian-Token: your-token" \
     -d '{"method": "jira_search", "params": {"jql": "assignee = currentUser()"}}'
```

### Multi-User Deployment

**Configuration:**
```bash
# .env file for multi-user mode
MCP_TRANSPORT=sse
MCP_PORT=9000
ATLASSIAN_MULTI_USER=true

# Optional: Default fallback credentials
ATLASSIAN_URL=https://company.atlassian.net
ATLASSIAN_EMAIL=fallback@company.com
ATLASSIAN_API_TOKEN=fallback-token
```

**Per-request authentication:**
```bash
# Using headers
curl -H "X-Atlassian-Email: user1@company.com" \
     -H "X-Atlassian-Token: user1-token" \
     -H "X-Atlassian-URL: https://company.atlassian.net" \
     http://localhost:9000/mcp/call

# Using query parameters
curl "http://localhost:9000/mcp/call?email=user1@company.com&token=user1-token"
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN uv sync --frozen --no-dev

# Expose port
EXPOSE 9000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9000/healthz || exit 1

# Run server
CMD ["uv", "run", "mcp-atlassian", "--transport", "sse", "--port", "9000", "--host", "0.0.0.0"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  mcp-atlassian:
    build: .
    ports:
      - "9000:9000"
    environment:
      - MCP_TRANSPORT=sse
      - MCP_PORT=9000
      - MCP_HOST=0.0.0.0
      - ATLASSIAN_URL=${ATLASSIAN_URL}
      - ATLASSIAN_EMAIL=${ATLASSIAN_EMAIL}
      - ATLASSIAN_API_TOKEN=${ATLASSIAN_API_TOKEN}
      - LOG_LEVEL=INFO
    env_file:
      - .env
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Optional: Nginx reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - mcp-atlassian
    restart: unless-stopped
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-atlassian
  labels:
    app: mcp-atlassian
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-atlassian
  template:
    metadata:
      labels:
        app: mcp-atlassian
    spec:
      containers:
      - name: mcp-atlassian
        image: mcp-atlassian:latest
        ports:
        - containerPort: 9000
        env:
        - name: MCP_TRANSPORT
          value: "sse"
        - name: MCP_PORT
          value: "9000"
        - name: MCP_HOST
          value: "0.0.0.0"
        envFrom:
        - secretRef:
            name: atlassian-credentials
        livenessProbe:
          httpGet:
            path: /healthz
            port: 9000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /healthz
            port: 9000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-atlassian-service
spec:
  selector:
    app: mcp-atlassian
  ports:
  - protocol: TCP
    port: 80
    targetPort: 9000
  type: LoadBalancer
---
apiVersion: v1
kind: Secret
metadata:
  name: atlassian-credentials
type: Opaque
data:
  ATLASSIAN_URL: base64-encoded-atlassian-url
  ATLASSIAN_EMAIL: base64-encoded-email
  ATLASSIAN_API_TOKEN: base64-encoded-token
```

## Production Deployment Considerations

### Security

1. **Credential Management:**
   ```bash
   # Use environment variables or secrets management
   export ATLASSIAN_API_TOKEN=$(vault kv get -field=token secret/atlassian)

   # Rotate tokens regularly
   # Monitor access logs
   # Use least-privilege principles
   ```

2. **Network Security:**
   ```bash
   # Use HTTPS in production
   # Implement rate limiting
   # Configure firewalls
   # Use VPN or private networks
   ```

3. **Authentication:**
   ```bash
   # Prefer OAuth 2.0 for production
   # Implement token refresh
   # Monitor authentication failures
   ```

### Monitoring and Logging

1. **Health Checks:**
   ```bash
   # Application health
   curl http://localhost:9000/healthz

   # Detailed health with metrics
   curl http://localhost:9000/healthz/detailed
   ```

2. **Metrics Collection:**
   ```bash
   # Enable Prometheus metrics
   export ENABLE_PROMETHEUS_METRICS=true

   # Metrics endpoint
   curl http://localhost:9000/metrics
   ```

3. **Structured Logging:**
   ```bash
   # JSON logging for production
   export LOG_FORMAT=json
   export LOG_LEVEL=INFO

   # Log aggregation
   # ELK Stack, Splunk, or CloudWatch
   ```

### Performance Optimization

1. **Caching:**
   ```bash
   # Enable Redis caching
   export REDIS_URL=redis://localhost:6379
   export CACHE_TTL=3600
   ```

2. **Connection Pooling:**
   ```bash
   # Configure connection limits
   export ATLASSIAN_MAX_CONNECTIONS=10
   export ATLASSIAN_POOL_SIZE=5
   ```

3. **Resource Limits:**
   ```bash
   # Memory and CPU limits
   export MAX_MEMORY=512MB
   export MAX_CPU_CORES=2
   ```

### Backup and Recovery

1. **Configuration Backup:**
   ```bash
   # Backup configurations
   tar -czf mcp-atlassian-config.tar.gz .env config/
   ```

2. **Token Management:**
   ```bash
   # Backup OAuth tokens
   # Document token refresh procedures
   # Maintain emergency access tokens
   ```

## Troubleshooting

### Common Issues

1. **Authentication Failures:**
   ```bash
   # Check credentials
   uv run mcp-atlassian --test-auth

   # Verify URLs
   curl -u email:token https://your-domain.atlassian.net/rest/api/3/myself
   ```

2. **Connection Issues:**
   ```bash
   # Test connectivity
   uv run mcp-atlassian --test-connection

   # Check SSL/TLS
   openssl s_client -connect your-domain.atlassian.net:443
   ```

3. **Performance Issues:**
   ```bash
   # Enable debug logging
   export LOG_LEVEL=DEBUG

   # Monitor metrics
   curl http://localhost:9000/healthz/detailed
   ```

### Debug Mode

```bash
# Enable comprehensive debugging
export LOG_LEVEL=DEBUG
export ATLASSIAN_LOG_LEVEL=DEBUG
export MCP_DEBUG=true

# Start with verbose output
uv run mcp-atlassian -vv --env-file .env
```

### Validation Tools

```bash
# Test configuration
uv run mcp-atlassian --validate-config

# Test authentication
uv run mcp-atlassian --test-auth

# Test MCP protocol
uv run mcp-atlassian --test-mcp

# Performance benchmark
uv run mcp-atlassian --benchmark
```

## Support and Resources

### Documentation
- [MCP Protocol Specification](https://github.com/modelcontextprotocol/specification)
- [Atlassian REST API Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [OAuth 2.0 Setup Guide](https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/)

### Community
- GitHub Issues: Report bugs and request features
- Discussions: Ask questions and share configurations
- Wiki: Community-contributed examples and guides

### Commercial Support
- Professional Services: Custom deployments and integrations
- Enterprise Support: SLA-backed support and prioritized fixes
- Training: Team training and best practices workshops

---

*This deployment guide ensures successful configuration of the MCP Atlassian server across all supported clients and deployment scenarios.*
