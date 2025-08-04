#!/bin/bash
set -euo pipefail

# ============================================================================
# MCP Atlassian Server Setup Script
# 
# A platform-agnostic setup script that works on macOS, Linux, and WSL.
# Handles environment setup, dependency installation, and configuration.
# ============================================================================

# Initialize pyenv if available (do this early)
if [[ -d "$HOME/.pyenv" ]]; then
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    if command -v pyenv &> /dev/null; then
        eval "$(pyenv init --path)" 2>/dev/null || true
        eval "$(pyenv init -)" 2>/dev/null || true
    fi
fi

# ----------------------------------------------------------------------------
# Constants and Configuration
# ----------------------------------------------------------------------------

# Colors for output (ANSI codes work on all platforms)
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[0;31m'
readonly NC='\033[0m' # No Color

# Configuration
readonly VENV_PATH=".mcp-atlassian_venv"

# ----------------------------------------------------------------------------
# Utility Functions
# ----------------------------------------------------------------------------

# Print colored output
print_success() {
    echo -e "${GREEN}✓${NC} $1" >&2
}

print_error() {
    echo -e "${RED}✗${NC} $1" >&2
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1" >&2
}

print_info() {
    echo -e "${YELLOW}$1${NC}" >&2
}

# Get the script's directory (works on all platforms)
get_script_dir() {
    cd "$(dirname "$0")" && pwd
}

# Clear Python cache files to prevent import issues
clear_python_cache() {
    print_info "Clearing Python cache files..."
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    print_success "Python cache cleared"
}

# ----------------------------------------------------------------------------
# Platform Detection Functions
# ----------------------------------------------------------------------------

# Get cross-platform Python executable path from venv
get_venv_python_path() {
    local venv_path="$1"
    
    # Check for both Unix and Windows Python executable paths
    if [[ -f "$venv_path/bin/python" ]]; then
        echo "$venv_path/bin/python"
    elif [[ -f "$venv_path/Scripts/python.exe" ]]; then
        echo "$venv_path/Scripts/python.exe"
    else
        return 1  # No Python executable found
    fi
}

# Detect the operating system
detect_os() {
    case "$OSTYPE" in
        darwin*)  echo "macos" ;;
        linux*)   
            if grep -qi microsoft /proc/version 2>/dev/null; then
                echo "wsl"
            else
                echo "linux"
            fi
            ;;
        msys*|cygwin*|win32) echo "windows" ;;
        *)        echo "unknown" ;;
    esac
}

# Get Claude config path based on platform
get_claude_config_path() {
    local os_type=$(detect_os)
    
    case "$os_type" in
        macos)
            echo "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
            ;;
        linux)
            echo "$HOME/.config/Claude/claude_desktop_config.json"
            ;;
        wsl)
            local win_appdata
            if command -v wslvar &> /dev/null; then
                win_appdata=$(wslvar APPDATA 2>/dev/null)
            fi
            
            if [[ -n "$win_appdata" ]]; then
                echo "$(wslpath "$win_appdata")/Claude/claude_desktop_config.json"
            else
                print_warning "Could not determine Windows user path automatically. Please ensure APPDATA is set correctly or provide the full path manually."
                echo "/mnt/c/Users/$USER/AppData/Roaming/Claude/claude_desktop_config.json"
            fi
            ;;
        windows)
            echo "$APPDATA/Claude/claude_desktop_config.json"
            ;;
        *)
            echo ""
            ;;
    esac
}

# Get Cursor config path (cross-platform)
get_cursor_config_path() {
    echo "$HOME/.cursor/mcp.json"
}

# ----------------------------------------------------------------------------
# Python Environment Functions
# ----------------------------------------------------------------------------

# Find suitable Python command
find_python() {
    # Pyenv should already be initialized at script start, but check if .python-version exists
    if [[ -f ".python-version" ]] && command -v pyenv &> /dev/null; then
        # Ensure pyenv respects the local .python-version
        pyenv local &>/dev/null || true
    fi
    
    # Prefer Python 3.12 for best compatibility
    local python_cmds=("python3.12" "python3.13" "python3.11" "python3.10" "python3" "python" "py")
    
    for cmd in "${python_cmds[@]}"; do
        if command -v "$cmd" &> /dev/null; then
            local version=$($cmd --version 2>&1)
            if [[ $version =~ Python\ 3\.([0-9]+)\.([0-9]+) ]]; then
                local major_version=${BASH_REMATCH[1]}
                local minor_version=${BASH_REMATCH[2]}
                
                # Check minimum version (3.10) for better library compatibility
                if [[ $major_version -ge 10 ]]; then
                    # Verify the command actually exists (important for pyenv)
                    if command -v "$cmd" &> /dev/null; then
                        echo "$cmd"
                        print_success "Found Python: $version"
                        
                        # Recommend Python 3.12
                        if [[ $major_version -ne 12 ]]; then
                            print_info "Note: Python 3.12 is recommended for best compatibility."
                        fi
                        
                        return 0
                    fi
                fi
            fi
        fi
    done
    
    print_error "Python 3.10+ not found. MCP Atlassian requires Python 3.10+."
    echo "" >&2
    
    local os_type=$(detect_os)
    if [[ "$os_type" == "macos" ]]; then
        echo "To install Python:" >&2
        echo "  brew install python@3.12" >&2
    elif [[ "$os_type" == "linux" || "$os_type" == "wsl" ]]; then
        echo "To install Python:" >&2
        echo "  Ubuntu/Debian: sudo apt update && sudo apt install -y python3.12 python3.12-venv python3.12-pip" >&2
        echo "  RHEL/CentOS:   sudo dnf install -y python3.12 python3.12-venv python3.12-pip" >&2
        echo "  Arch:          sudo pacman -S python python-pip" >&2
    fi
    echo "" >&2
    
    return 1
}

# Setup virtual environment
setup_venv() {
    local python_cmd="$1"
    local venv_python=""
    local venv_pip=""
    
    # Create venv if it doesn't exist
    if [[ ! -d "$VENV_PATH" ]]; then
        print_info "Creating isolated environment..."
        
        # Try creating virtual environment
        if $python_cmd -m venv "$VENV_PATH" >/dev/null 2>&1; then
            print_success "Created isolated environment"
        else
            print_error "Failed to create virtual environment"
            echo "" >&2
            echo "Your system may be missing Python development packages." >&2
            echo "Please install python3-venv or python3-dev packages for your system." >&2
            exit 1
        fi
    fi
    
    # Get venv Python path based on platform
    venv_python=$(get_venv_python_path "$VENV_PATH")
    if [[ $? -ne 0 ]]; then
        print_error "Virtual environment Python not found"
        exit 1
    fi
    
    # Verify pip is working
    if ! $venv_python -m pip --version &>/dev/null 2>&1; then
        print_error "pip is not working correctly in the virtual environment"
        echo "" >&2
        echo "Try deleting the virtual environment and running again:" >&2
        echo "  rm -rf $VENV_PATH" >&2
        echo "  ./install-server.sh" >&2
        exit 1
    fi
    
    print_success "Virtual environment ready with pip"
    
    # Convert to absolute path for MCP registration
    local abs_venv_python=$(cd "$(dirname "$venv_python")" && pwd)/$(basename "$venv_python")
    echo "$abs_venv_python"
    return 0
}

# Check if package is installed
check_package() {
    local python_cmd="$1"
    local package="$2"
    $python_cmd -c "import $package" 2>/dev/null
}

# Install dependencies using uv
install_dependencies() {
    local python_cmd="$1"
    
    # Check if uv is available in the venv
    if ! $python_cmd -m pip show uv &>/dev/null; then
        print_info "Installing uv package manager..."
        $python_cmd -m pip install -q uv
        print_success "uv installed"
    fi
    
    # Check if project dependencies are already installed
    if $python_cmd -c "import mcp_atlassian" 2>/dev/null; then
        print_success "Dependencies already installed"
        return 0
    fi
    
    echo ""
    print_info "Setting up MCP Atlassian Server..."
    echo "Installing required components:"
    echo "  • FastMCP protocol library"
    echo "  • Atlassian API clients"
    echo "  • Data validation and formatting"
    echo "  • OAuth and security components"
    echo ""
    
    # Use uv to install from pyproject.toml
    local install_cmd="$python_cmd -m uv sync --all-extras"
    
    echo -n "Downloading packages..."
    local install_output
    
    # Capture both stdout and stderr
    install_output=$($install_cmd 2>&1)
    local exit_code=$?
    
    if [[ $exit_code -ne 0 ]]; then
        echo -e "\r${RED}✗ Setup failed${NC}                      "
        echo ""
        echo "Installation error:"
        echo "$install_output" | head -20
        echo ""
        echo "Try running manually:"
        echo "  $python_cmd -m uv sync --all-extras"
        return 1
    else
        echo -e "\r${GREEN}✓ Setup complete!${NC}                    "
        return 0
    fi
}

# ----------------------------------------------------------------------------
# Environment Configuration Functions
# ----------------------------------------------------------------------------

# Setup .env file
setup_env_file() {
    if [[ -f .env ]]; then
        print_success ".env file already exists"
        return 0
    fi
    
    print_info "Creating .env file with example configuration..."
    
    cat > .env << 'EOF'
# Atlassian Configuration
# Choose one authentication method and configure the appropriate settings

# Method 1: API Token (Cloud) - Recommended for Cloud instances
# ATLASSIAN_URL=https://your-domain.atlassian.net
# ATLASSIAN_USERNAME=your-email@example.com
# ATLASSIAN_TOKEN=your-api-token

# Method 2: Personal Access Token (Server/DC)
# ATLASSIAN_URL=https://your-jira-server.company.com
# ATLASSIAN_PAT=your-personal-access-token

# Method 3: OAuth 2.0 (Cloud) - Advanced users
# ATLASSIAN_URL=https://your-domain.atlassian.net
# ATLASSIAN_OAUTH_CLIENT_ID=your-oauth-client-id
# ATLASSIAN_OAUTH_CLIENT_SECRET=your-oauth-client-secret

# Optional: Proxy Configuration (if behind corporate firewall)
# HTTP_PROXY=http://proxy.company.com:8080
# HTTPS_PROXY=http://proxy.company.com:8080

# Optional: Custom Headers (for corporate environments)
# ATLASSIAN_CUSTOM_HEADERS={"X-Custom-Header": "value"}

# Optional: SSL Configuration
# SSL_VERIFY=true
# SSL_CERT_PATH=/path/to/certificate.pem

# Optional: Filtering (limit access to specific projects/spaces)
# JIRA_PROJECTS_FILTER=PROJ1,PROJ2,PROJ3
# CONFLUENCE_SPACES_FILTER=SPACE1,SPACE2

# Optional: Tool Configuration
# TOOLS_ENABLED=all
# READ_ONLY_MODE=false

# Optional: Logging
# LOG_LEVEL=INFO
# LOG_FORMAT=json
EOF
    
    print_success "Created .env file with example configuration"
    print_warning "Please edit .env and configure your Atlassian credentials!"
    
    return 0
}

# Validate configuration
validate_config() {
    local has_config=false
    
    # Source the .env file to check values
    if [[ -f .env ]]; then
        set -a
        source .env 2>/dev/null || true
        set +a
    fi
    
    # Check for any valid authentication method
    if [[ -n "${ATLASSIAN_URL:-}" ]]; then
        print_success "ATLASSIAN_URL configured"
        has_config=true
        
        if [[ -n "${ATLASSIAN_TOKEN:-}" && -n "${ATLASSIAN_USERNAME:-}" ]]; then
            print_success "API Token authentication configured"
        elif [[ -n "${ATLASSIAN_PAT:-}" ]]; then
            print_success "Personal Access Token authentication configured"
        elif [[ -n "${ATLASSIAN_OAUTH_CLIENT_ID:-}" && -n "${ATLASSIAN_OAUTH_CLIENT_SECRET:-}" ]]; then
            print_success "OAuth 2.0 authentication configured"
        else
            has_config=false
        fi
    fi
    
    if [[ "$has_config" == false ]]; then
        print_error "Atlassian credentials not found in .env!"
        echo "" >&2
        echo "Please edit .env and configure your Atlassian connection:" >&2
        echo "" >&2
        echo "For Cloud instances (recommended):" >&2
        echo "  ATLASSIAN_URL=https://your-domain.atlassian.net" >&2
        echo "  ATLASSIAN_USERNAME=your-email@example.com" >&2
        echo "  ATLASSIAN_TOKEN=your-api-token" >&2
        echo "" >&2
        echo "For Server/DC instances:" >&2
        echo "  ATLASSIAN_URL=https://your-server.company.com" >&2
        echo "  ATLASSIAN_PAT=your-personal-access-token" >&2
        echo "" >&2
        echo "API tokens can be created at:" >&2
        echo "  https://id.atlassian.com/manage-profile/security/api-tokens" >&2
        echo "" >&2
        print_info "After adding your credentials, run ./install-server.sh again" >&2
        echo "" >&2
        return 1
    fi
    
    return 0
}

# ----------------------------------------------------------------------------
# IDE Integration Functions
# ----------------------------------------------------------------------------

# Shared function to update IDE configuration with proper duplicate detection
update_ide_config() {
    local ide_name="$1"
    local config_path="$2"
    local python_cmd="$3"
    local server_args="$4"
    
    # Create config directory if it doesn't exist
    local config_dir=$(dirname "$config_path")
    mkdir -p "$config_dir" 2>/dev/null || true
    
    # Handle existing config
    if [[ -f "$config_path" ]]; then
        # Add new config with duplicate detection
        local temp_file=$(mktemp)
        python3 -c "
import json
import sys

try:
    with open('$config_path', 'r') as f:
        config = json.load(f)
except Exception as e:
    print('Warning: Could not parse existing config file, creating new one')
    config = {}

# Ensure mcpServers exists
if 'mcpServers' not in config:
    config['mcpServers'] = {}

# Check if mcp-atlassian server already exists
new_config = {
    'command': '$python_cmd',
    'args': ['$server_args']
}

if 'mcp-atlassian' in config['mcpServers']:
    existing_config = config['mcpServers']['mcp-atlassian']
    if existing_config == new_config:
        print('ALREADY_CONFIGURED')
        sys.exit(0)
    else:
        print('UPDATING_EXISTING')
        print('Old config:', json.dumps(existing_config, indent=2))
        print('New config:', json.dumps(new_config, indent=2))
else:
    print('ADDING_NEW')

# Add/update mcp-atlassian server
config['mcpServers']['mcp-atlassian'] = new_config

with open('$temp_file', 'w') as f:
    json.dump(config, f, indent=2)
" 2>/dev/null
        
        local python_exit_code=$?
        local python_output=$(python3 -c "
import json
import sys

try:
    with open('$config_path', 'r') as f:
        config = json.load(f)
except Exception as e:
    print('Warning: Could not parse existing config file, creating new one')
    config = {}

# Ensure mcpServers exists
if 'mcpServers' not in config:
    config['mcpServers'] = {}

# Check if mcp-atlassian server already exists
new_config = {
    'command': '$python_cmd',
    'args': ['$server_args']
}

if 'mcp-atlassian' in config['mcpServers']:
    existing_config = config['mcpServers']['mcp-atlassian']
    if existing_config == new_config:
        print('ALREADY_CONFIGURED')
        sys.exit(0)
    else:
        print('UPDATING_EXISTING')
else:
    print('ADDING_NEW')

# Add/update mcp-atlassian server
config['mcpServers']['mcp-atlassian'] = new_config

with open('$temp_file', 'w') as f:
    json.dump(config, f, indent=2)
" 2>&1)
        
        # Handle different scenarios based on Python output
        if [[ "$python_output" == "ALREADY_CONFIGURED" ]]; then
            print_success "$ide_name configuration is already up to date"
            echo "  Config: $config_path"
            rm -f "$temp_file" 2>/dev/null || true
            return 0
        elif [[ "$python_output" == "UPDATING_EXISTING" ]]; then
            print_info "Updating existing $ide_name 'mcp-atlassian' server configuration..."
            echo "  Previous configuration will be overwritten"
        elif [[ "$python_output" == "ADDING_NEW" ]]; then
            print_info "Adding 'mcp-atlassian' server to existing $ide_name configuration..."
        else
            print_info "Updating existing $ide_name config..."
        fi
        
        # Move temp file to final location if Python succeeded
        if [[ $python_exit_code -eq 0 ]] && [[ -f "$temp_file" ]] && mv "$temp_file" "$config_path"; then
            print_success "Successfully configured $ide_name"
            echo "  Config: $config_path"
            echo "  Restart $ide_name to use the new MCP server"
        else
            rm -f "$temp_file" 2>/dev/null || true
            print_error "Failed to update $ide_name config"
            echo "Manual config location: $config_path"
            echo "Add this configuration:"
            cat << EOF
{
  "mcpServers": {
    "mcp-atlassian": {
      "command": "$python_cmd",
      "args": ["$server_args"]
    }
  }
}
EOF
        fi
        
    else
        print_info "Creating new $ide_name config..."
        cat > "$config_path" << EOF
{
  "mcpServers": {
    "mcp-atlassian": {
      "command": "$python_cmd",
      "args": ["$server_args"]
    }
  }
}
EOF
        
        if [[ $? -eq 0 ]]; then
            print_success "Successfully configured $ide_name"
            echo "  Config: $config_path"
            echo "  Restart $ide_name to use the new MCP server"
        else
            print_error "Failed to create $ide_name config"
            echo "Manual config location: $config_path"
            echo "Add this configuration:"
            cat << EOF
{
  "mcpServers": {
    "mcp-atlassian": {
      "command": "$python_cmd",
      "args": ["$server_args"]
    }
  }
}
EOF
        fi
    fi
}

# Check and update Claude Desktop configuration
check_claude_desktop_integration() {
    local python_cmd="$1"
    local server_args="$2"
    
    local config_path=$(get_claude_config_path)
    if [[ -z "$config_path" ]]; then
        print_warning "Unable to determine Claude Desktop config path for this platform"
        return 0
    fi
    
    echo ""
    read -p "Configure MCP Atlassian for Claude Desktop? (Y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        print_info "Skipping Claude Desktop integration"
        return 0
    fi
    
    # Use shared configuration function
    update_ide_config "Claude Desktop" "$config_path" "$python_cmd" "$server_args"
}

# Check and update Cursor IDE configuration
check_cursor_ide_integration() {
    local python_cmd="$1"
    local server_args="$2"
    
    local config_path=$(get_cursor_config_path)
    
    echo ""
    read -p "Configure MCP Atlassian for Cursor IDE? (Y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        print_info "Skipping Cursor IDE integration"
        return 0
    fi
    
    # Use shared configuration function
    update_ide_config "Cursor IDE" "$config_path" "$python_cmd" "$server_args"
}

# Display configuration instructions
display_config_instructions() {
    local python_cmd="$1"
    local server_args="$2"
    
    echo ""
    local config_header="MCP ATLASSIAN SERVER CONFIGURATION"
    echo "===== $config_header ====="
    printf '%*s\n' "$((${#config_header} + 12))" | tr ' ' '='
    echo ""
    echo "To use MCP Atlassian Server with your Claude clients:"
    echo ""
    
    print_info "1. For Claude Desktop:"
    echo "   Add this configuration to your Claude Desktop config file:"
    echo ""
    cat << EOF
   {
     "mcpServers": {
       "mcp-atlassian": {
         "command": "$python_cmd",
         "args": ["$server_args"]
       }
     }
   }
EOF
    
    # Show platform-specific config location
    local config_path=$(get_claude_config_path)
    if [[ -n "$config_path" ]]; then
        echo ""
        print_info "   Config file location:"
        echo -e "   ${YELLOW}$config_path${NC}"
    fi
    
    echo ""
    print_info "2. For Cursor IDE:"
    echo "   Add this configuration to your Cursor IDE config file:"
    echo ""
    cat << EOF
   {
     "mcpServers": {
       "mcp-atlassian": {
         "command": "$python_cmd",
         "args": ["$server_args"]
       }
     }
   }
EOF
    
    local cursor_config_path=$(get_cursor_config_path)
    echo ""
    print_info "   Config file location:"
    echo -e "   ${YELLOW}$cursor_config_path${NC}"
    echo ""
    
    print_info "3. Restart Claude Desktop/Cursor IDE after updating config files"
    echo ""
    
    print_info "4. For FastMCP CLI:"
    echo -e "   ${GREEN}fastmcp run mcp-atlassian${NC}"
    echo ""
}

# Display setup instructions
display_setup_instructions() {
    local python_cmd="$1"
    local server_args="$2"
    
    echo ""
    local setup_header="SETUP COMPLETE"
    echo "===== $setup_header ====="
    printf '%*s\n' "$((${#setup_header} + 12))" | tr ' ' '='
    echo ""
    print_success "MCP Atlassian Server is ready to use!"
    echo ""
    print_info "Quick Test:"
    echo "  $python_cmd -m mcp_atlassian"
    echo ""
    print_info "With environment file:"
    echo "  $python_cmd -m mcp_atlassian --env-file .env"
    echo ""
    print_info "With verbose logging:"
    echo "  $python_cmd -m mcp_atlassian -vv"
    echo ""
    print_info "OAuth setup wizard:"
    echo "  $python_cmd -m mcp_atlassian --oauth-setup -v"
    echo ""
    print_info "FastMCP CLI:"
    echo "  fastmcp run mcp-atlassian"
    echo ""
}

# ----------------------------------------------------------------------------
# Main Function
# ----------------------------------------------------------------------------

# Show help message
show_help() {
    local header="🔧 MCP Atlassian Server Setup"
    echo "$header"
    printf '%*s\n' "${#header}" | tr ' ' '='
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help      Show this help message"
    echo "  -c, --config    Show configuration instructions for Claude clients"
    echo "  --clear-cache   Clear Python cache and exit (helpful for import issues)"
    echo ""
    echo "Examples:"
    echo "  $0              Setup the MCP server"
    echo "  $0 -c           Show configuration instructions"
    echo "  $0 --clear-cache Clear Python cache (fixes import issues)"
    echo ""
    echo "For more information, visit:"
    echo "  https://github.com/your-username/mcp-atlassian"
}

main() {
    # Parse command line arguments
    local arg="${1:-}"
    
    case "$arg" in
        -h|--help)
            show_help
            exit 0
            ;;
        -c|--config)
            # Setup minimal environment to get paths for config display
            echo "Setting up environment for configuration display..."
            echo ""
            local python_cmd
            python_cmd=$(find_python) || exit 1
            python_cmd=$(setup_venv "$python_cmd") || exit 1
            local server_args="-m mcp_atlassian"
            display_config_instructions "$python_cmd" "$server_args"
            exit 0
            ;;
        --clear-cache)
            # Clear cache and exit
            clear_python_cache
            print_success "Cache cleared successfully"
            echo ""
            echo "You can now run './install-server.sh' normally"
            exit 0
            ;;
        "")
            # Normal setup
            ;;
        *)
            print_error "Unknown option: $arg"
            echo "" >&2
            show_help
            exit 1
            ;;
    esac
    
    # Display header
    local main_header="🔧 MCP Atlassian Server Setup"
    echo "$main_header"
    printf '%*s\n' "${#main_header}" | tr ' ' '='
    echo ""
    
    # Check if venv exists
    if [[ ! -d "$VENV_PATH" ]]; then
        echo "Setting up Python environment for first time..."
    fi
    
    # Step 1: Clear Python cache to prevent import issues
    clear_python_cache
    
    # Step 2: Setup environment file
    setup_env_file || exit 1
    
    # Step 3: Setup Python environment
    local python_cmd
    python_cmd=$(find_python) || exit 1
    python_cmd=$(setup_venv "$python_cmd") || exit 1
    
    # Step 4: Install dependencies
    install_dependencies "$python_cmd" || exit 1
    
    # Step 5: Set server args
    local server_args="-m mcp_atlassian"
    
    # Step 6: Display setup instructions
    display_setup_instructions "$python_cmd" "$server_args"
    
    # Step 7: Validate configuration (but don't fail if not configured yet)
    echo ""
    print_info "Checking configuration..."
    if validate_config; then
        print_success "Configuration looks good!"
    else
        print_warning "Please configure your Atlassian credentials in .env before using the server"
    fi
    
    # Step 8: Check Claude Desktop integration
    check_claude_desktop_integration "$python_cmd" "$server_args"
    
    # Step 9: Check Cursor IDE integration
    check_cursor_ide_integration "$python_cmd" "$server_args"
    
    echo ""
    echo "To show config: ./install-server.sh -c"
    echo ""
    echo "Happy coding! 🎉"
}

# ----------------------------------------------------------------------------
# Script Entry Point
# ----------------------------------------------------------------------------

# Run main function with all arguments
main "$@"