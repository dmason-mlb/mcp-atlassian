# MCP Client Configuration Guide

**Created:** July 30, 2025
**Version:** 1.0.0
**Purpose:** Detailed configuration instructions for MCP Atlassian server across different MCP clients

## Overview

This guide provides step-by-step configuration instructions for connecting the MCP Atlassian server to various MCP-compatible clients including Claude Code, Cursor, Claude Desktop, VS Code, and other AI assistants.

## Prerequisites

Before configuring any MCP client, ensure you have:

1. **MCP Atlassian server installed and working:**
   ```bash
   cd /path/to/mcp-atlassian
   uv run mcp-atlassian --test-auth --env-file .env
   ```

2. **Valid authentication configured** (API token, OAuth, or PAT)

3. **Required environment variables** set in `.env` file

## Client Configuration

### Claude Code (Anthropic Official CLI)

Claude Code is Anthropic's official command-line interface that supports MCP servers.

#### Installation

```bash
# Install via npm (recommended)
npm install -g @anthropic-ai/claude-code

# Verify installation
claude-code --version

# Alternative: Direct download
curl -sSL https://install.claudecode.com | bash
```

#### Configuration Method 1: Global MCP Config

1. **Create MCP configuration directory:**
   ```bash
   mkdir -p ~/.claude/mcp
   ```

2. **Create configuration file:**
   ```bash
   cat > ~/.claude/mcp/config.json << 'EOF'
   {
     "servers": {
       "atlassian": {
         "command": "uv",
         "args": ["run", "mcp-atlassian"],
         "cwd": "/Users/yourusername/path/to/mcp-atlassian",
         "env": {
           "ATLASSIAN_EMAIL": "your-email@company.com",
           "ATLASSIAN_API_TOKEN": "your-api-token",
           "JIRA_URL": "https://your-domain.atlassian.net",
           "CONFLUENCE_URL": "https://your-domain.atlassian.net/wiki",
           "LOG_LEVEL": "INFO"
         }
       }
     }
   }
   EOF
   ```

3. **Test the configuration:**
   ```bash
   claude-code list-servers
   claude-code test-server atlassian
   ```

#### Configuration Method 2: Environment File

1. **Use existing .env file:**
   ```bash
   cat > ~/.claude/mcp/config.json << 'EOF'
   {
     "servers": {
       "atlassian": {
         "command": "uv",
         "args": ["run", "mcp-atlassian", "--env-file", "/path/to/mcp-atlassian/.env"],
         "cwd": "/path/to/mcp-atlassian"
       }
     }
   }
   EOF
   ```

#### Configuration Method 3: Project-Specific

1. **Create project-level MCP config:**
   ```bash
   # In your project directory
   mkdir -p .claude/mcp
   cat > .claude/mcp/config.json << 'EOF'
   {
     "servers": {
       "atlassian": {
         "command": "uv",
         "args": ["run", "mcp-atlassian", "--env-file", ".env"],
         "cwd": "/path/to/mcp-atlassian"
       }
     }
   }
   EOF
   ```

#### Usage

```bash
# Start Claude Code with MCP
claude-code --mcp

# Start in specific project
cd /path/to/your/project
claude-code --mcp

# Use specific MCP config
claude-code --mcp-config /path/to/custom/config.json
```

#### Troubleshooting Claude Code

```bash
# Debug MCP connection
claude-code --debug --mcp

# Test server connectivity
claude-code test-server atlassian --verbose

# Check logs
tail -f ~/.claude/logs/mcp.log
```

### Cursor IDE

Cursor is a popular AI-powered code editor with native MCP support.

#### Installation

1. **Download Cursor:**
   - Visit [cursor.sh](https://cursor.sh)
   - Download for your platform
   - Install the application

#### Configuration Method 1: Settings UI

1. **Open Cursor Settings:**
   - Press `Cmd/Ctrl + ,`
   - Go to **Extensions** → **MCP**

2. **Add MCP Server:**
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

#### Configuration Method 2: Config File

1. **Locate Cursor config directory:**
   - **macOS:** `~/Library/Application Support/Cursor/User/`
   - **Windows:** `%APPDATA%\Cursor\User\`
   - **Linux:** `~/.config/Cursor/User/`

2. **Create or edit `settings.json`:**
   ```json
   {
     "mcp.servers": {
       "atlassian": {
         "command": "uv",
         "args": ["run", "mcp-atlassian", "--env-file", "/path/to/.env"],
         "cwd": "/path/to/mcp-atlassian"
       }
     }
   }
   ```

#### Configuration Method 3: Workspace-Specific

1. **Create workspace MCP config:**
   ```bash
   # In your project root
   mkdir -p .vscode
   cat > .vscode/settings.json << 'EOF'
   {
     "mcp.servers": {
       "atlassian": {
         "command": "uv",
         "args": ["run", "mcp-atlassian"],
         "cwd": "/path/to/mcp-atlassian",
         "env": {
           "ATLASSIAN_EMAIL": "your-email@company.com",
           "ATLASSIAN_API_TOKEN": "your-api-token",
           "JIRA_URL": "https://your-domain.atlassian.net"
         }
       }
     }
   }
   EOF
   ```

#### Usage in Cursor

1. **Verify MCP Connection:**
   - Check status bar for MCP indicator
   - Open Command Palette (`Cmd/Ctrl + Shift + P`)
   - Search for "MCP: Show Servers"

2. **Use Atlassian Tools:**
   - Open AI chat panel
   - Ask: "Search for my assigned Jira issues"
   - Use: "Create a new Jira issue for this bug"

#### Troubleshooting Cursor

```bash
# Check Cursor logs
# macOS
tail -f ~/Library/Logs/Cursor/main.log

# Windows
type %APPDATA%\Cursor\logs\main.log

# Linux
tail -f ~/.config/Cursor/logs/main.log
```

### Claude Desktop (Anthropic)

Claude Desktop is Anthropic's desktop application with MCP support.

#### Installation

1. **Download Claude Desktop:**
   - Visit [claude.ai](https://claude.ai)
   - Download desktop app
   - Install and sign in

#### Configuration

1. **Locate config directory:**
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
           "ATLASSIAN_EMAIL": "your-email@company.com",
           "ATLASSIAN_API_TOKEN": "your-api-token",
           "JIRA_URL": "https://your-domain.atlassian.net",
           "CONFLUENCE_URL": "https://your-domain.atlassian.net/wiki"
         }
       }
     }
   }
   ```

3. **Alternative with environment file:**
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

#### Usage

1. **Verify Connection:**
   - Look for Atlassian tools in the interface
   - Try: "What are my open Jira issues?"

2. **Common Commands:**
   - "Search Jira for issues assigned to me"
   - "Create a new Confluence page"
   - "Show me recent activity in project XYZ"

### VS Code with MCP Extension

VS Code supports MCP through community extensions.

#### Installation

1. **Install MCP Extension:**
   - Open VS Code
   - Go to Extensions (`Ctrl+Shift+X`)
   - Search for "MCP" or "Model Context Protocol"
   - Install the extension

#### Configuration

1. **Open VS Code Settings:**
   - Press `Ctrl/Cmd + ,`
   - Switch to JSON view

2. **Add MCP server configuration:**
   ```json
   {
     "mcp.servers": {
       "atlassian": {
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
     },
     "mcp.enableDebugLogging": true
   }
   ```

#### Workspace Configuration

```json
{
  "mcp.servers": {
    "atlassian": {
      "command": "uv",
      "args": ["run", "mcp-atlassian", "--env-file", "${workspaceFolder}/../mcp-atlassian/.env"],
      "cwd": "${workspaceFolder}/../mcp-atlassian"
    }
  }
}
```

### Other MCP Clients

#### Continue.dev

```json
{
  "mcpServers": {
    "atlassian": {
      "command": "uv",
      "args": ["run", "mcp-atlassian"],
      "cwd": "/path/to/mcp-atlassian",
      "env": {
        "ATLASSIAN_EMAIL": "your-email@company.com",
        "ATLASSIAN_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

#### Zed Editor

```json
{
  "mcp_servers": {
    "atlassian": {
      "command": "uv",
      "args": ["run", "mcp-atlassian", "--env-file", "/path/to/.env"],
      "working_directory": "/path/to/mcp-atlassian"
    }
  }
}
```

#### Custom MCP Client

```bash
# STDIO connection
uv run mcp-atlassian --env-file .env

# HTTP SSE connection
uv run mcp-atlassian --transport sse --port 9000 --env-file .env

# Connect via curl
curl -N -H "Accept: text/event-stream" http://localhost:9000/sse
```

## Advanced Configuration

### Environment-Specific Configs

#### Development Environment

```json
{
  "servers": {
    "atlassian-dev": {
      "command": "uv",
      "args": ["run", "mcp-atlassian"],
      "cwd": "/path/to/mcp-atlassian",
      "env": {
        "ATLASSIAN_EMAIL": "dev@company.com",
        "ATLASSIAN_API_TOKEN": "dev-token",
        "JIRA_URL": "https://dev.atlassian.net",
        "LOG_LEVEL": "DEBUG",
        "JIRA_PROJECTS_FILTER": "DEV,TEST"
      }
    }
  }
}
```

#### Production Environment

```json
{
  "servers": {
    "atlassian-prod": {
      "command": "uv",
      "args": ["run", "mcp-atlassian"],
      "cwd": "/path/to/mcp-atlassian",
      "env": {
        "ATLASSIAN_EMAIL": "prod@company.com",
        "ATLASSIAN_API_TOKEN": "prod-token",
        "JIRA_URL": "https://company.atlassian.net",
        "LOG_LEVEL": "INFO",
        "ATLASSIAN_READ_ONLY": "true"
      }
    }
  }
}
```

### Multi-Instance Configuration

```json
{
  "servers": {
    "atlassian-main": {
      "command": "uv",
      "args": ["run", "mcp-atlassian"],
      "cwd": "/path/to/mcp-atlassian",
      "env": {
        "JIRA_URL": "https://main.atlassian.net",
        "ATLASSIAN_EMAIL": "user@company.com",
        "ATLASSIAN_API_TOKEN": "main-token"
      }
    },
    "atlassian-customer": {
      "command": "uv",
      "args": ["run", "mcp-atlassian"],
      "cwd": "/path/to/mcp-atlassian",
      "env": {
        "JIRA_URL": "https://customer.atlassian.net",
        "ATLASSIAN_EMAIL": "user@customer.com",
        "ATLASSIAN_API_TOKEN": "customer-token"
      }
    }
  }
}
```

### OAuth Configuration

```json
{
  "servers": {
    "atlassian-oauth": {
      "command": "uv",
      "args": ["run", "mcp-atlassian"],
      "cwd": "/path/to/mcp-atlassian",
      "env": {
        "ATLASSIAN_OAUTH_CLIENT_ID": "your-client-id",
        "ATLASSIAN_OAUTH_CLIENT_SECRET": "your-client-secret",
        "ATLASSIAN_OAUTH_REDIRECT_URI": "http://localhost:8000/callback",
        "JIRA_URL": "https://company.atlassian.net",
        "CONFLUENCE_URL": "https://company.atlassian.net/wiki"
      }
    }
  }
}
```

## Testing and Validation

### Test MCP Connection

```bash
# Test server startup
uv run mcp-atlassian --test-connection --env-file .env

# Test authentication
uv run mcp-atlassian --test-auth --env-file .env

# Test MCP protocol
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}}}' | uv run mcp-atlassian --env-file .env
```

### Client-Specific Testing

#### Claude Code
```bash
claude-code test-server atlassian
claude-code --debug --mcp
```

#### Cursor
1. Open Command Palette
2. Run "MCP: Test Server Connection"
3. Check "MCP: Show Server Logs"

#### Claude Desktop
1. Check for MCP indicator in UI
2. Try sample command: "List my Jira projects"

### Common Test Commands

Once connected, test these commands in your MCP client:

```
# Jira Testing
- "What are my assigned Jira issues?"
- "Search for issues in project ABC"
- "Show me recent issues updated in the last week"
- "Create a new issue in project XYZ"

# Confluence Testing
- "Search Confluence for documentation"
- "Show me recent Confluence pages"
- "List spaces I have access to"
- "Create a new Confluence page"

# General Testing
- "What Atlassian tools are available?"
- "Help me understand the Jira search syntax"
- "Show me my Atlassian instance information"
```

## Troubleshooting

### Common Issues

#### 1. "Command not found: uv"

**Solution:**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or use pip
pip install uv

# Verify installation
uv --version
```

#### 2. "Permission denied" errors

**Solution:**
```bash
# Check file permissions
ls -la /path/to/mcp-atlassian

# Fix permissions
chmod +x /path/to/mcp-atlassian/.venv/bin/python

# Ensure virtual environment is activated
source /path/to/mcp-atlassian/.venv/bin/activate
```

#### 3. "Authentication failed"

**Solution:**
```bash
# Test credentials manually
curl -u email:token https://your-domain.atlassian.net/rest/api/3/myself

# Check environment variables
uv run mcp-atlassian --test-auth --env-file .env

# Verify token permissions
```

#### 4. "Server not responding"

**Solution:**
```bash
# Check server startup
uv run mcp-atlassian --test-connection -v

# Check logs
export LOG_LEVEL=DEBUG
uv run mcp-atlassian --env-file .env

# Verify paths in config
```

#### 5. "Module not found" errors

**Solution:**
```bash
# Reinstall dependencies
cd /path/to/mcp-atlassian
uv sync --frozen

# Check Python path
which python
uv run which python
```

### Debug Mode

Enable debug mode for detailed troubleshooting:

```bash
# Environment variables
export LOG_LEVEL=DEBUG
export MCP_DEBUG=true

# Start with verbose output
uv run mcp-atlassian -vv --env-file .env
```

### Log Locations

#### Claude Code
```bash
# macOS/Linux
tail -f ~/.claude/logs/mcp.log

# Windows
type %USERPROFILE%\.claude\logs\mcp.log
```

#### Cursor
```bash
# macOS
tail -f ~/Library/Logs/Cursor/main.log

# Windows
type %APPDATA%\Cursor\logs\main.log

# Linux
tail -f ~/.config/Cursor/logs/main.log
```

#### Claude Desktop
```bash
# macOS
tail -f ~/Library/Logs/Claude/main.log

# Windows
type %APPDATA%\Claude\logs\main.log
```

## Best Practices

### Security
1. **Use environment files** instead of hardcoding credentials
2. **Restrict API token permissions** to minimum required
3. **Rotate tokens regularly**
4. **Use OAuth 2.0** for production deployments
5. **Never commit credentials** to version control

### Performance
1. **Use project-specific filters** (`JIRA_PROJECTS_FILTER`)
2. **Enable caching** where appropriate
3. **Monitor resource usage**
4. **Use read-only mode** for analytical tasks

### Maintenance
1. **Keep MCP server updated**
2. **Monitor logs** for errors
3. **Test connections** regularly
4. **Document configurations** for team members
5. **Have backup authentication** methods

---

*This configuration guide ensures successful setup of the MCP Atlassian server across all supported MCP clients and development environments.*
