"""Environment variable utility functions for MCP Atlassian."""

import os


def is_env_truthy(env_var_name: str, default: str = "") -> bool:
    """Check if environment variable is set to a standard truthy value.

    Considers 'true', '1', 'yes' as truthy values (case-insensitive).
    Used for most MCP environment variables.

    Args:
        env_var_name: Name of the environment variable to check
        default: Default value if environment variable is not set

    Returns:
        True if the environment variable is set to a truthy value, False otherwise
    """
    return os.getenv(env_var_name, default).lower() in ("true", "1", "yes")


def is_env_extended_truthy(env_var_name: str, default: str = "") -> bool:
    """Check if environment variable is set to an extended truthy value.

    Considers 'true', '1', 'yes', 'y', 'on' as truthy values (case-insensitive).
    Used for READ_ONLY_MODE and similar flags.

    Args:
        env_var_name: Name of the environment variable to check
        default: Default value if environment variable is not set

    Returns:
        True if the environment variable is set to a truthy value, False otherwise
    """
    return os.getenv(env_var_name, default).lower() in ("true", "1", "yes", "y", "on")


def is_env_ssl_verify(env_var_name: str, default: str = "true") -> bool:
    """Check SSL verification setting with secure defaults.

    Defaults to true unless explicitly set to false values.
    Used for SSL_VERIFY environment variables.

    Args:
        env_var_name: Name of the environment variable to check
        default: Default value if environment variable is not set

    Returns:
        True unless explicitly set to false values
    """
    return os.getenv(env_var_name, default).lower() not in ("false", "0", "no")


def get_custom_headers(env_var_name: str) -> dict[str, str]:
    """Parse custom headers from environment variable containing comma-separated key=value pairs.

    Args:
        env_var_name: Name of the environment variable to read

    Returns:
        Dictionary of parsed headers

    Examples:
        >>> # With CUSTOM_HEADERS="X-Custom=value1,X-Other=value2"
        >>> parse_custom_headers("CUSTOM_HEADERS")
        {'X-Custom': 'value1', 'X-Other': 'value2'}
        >>> # With unset environment variable
        >>> parse_custom_headers("UNSET_VAR")
        {}
    """
    header_string = os.getenv(env_var_name)
    if not header_string or not header_string.strip():
        return {}

    headers = {}
    pairs = header_string.split(",")

    for pair in pairs:
        pair = pair.strip()
        if not pair:
            continue

        if "=" not in pair:
            continue

        key, value = pair.split("=", 1)  # Split on first = only
        key = key.strip()
        value = value.strip()

        if key:  # Only add if key is not empty
            headers[key] = value

    return headers


def get_adf_rollout_percentage() -> int:
    """Get the ADF rollout percentage from environment variables.
    
    This enables gradual rollout of ADF format conversion by specifying 
    what percentage of requests should use ADF format.
    
    Returns:
        Percentage (0-100) of requests that should use ADF format.
        Default is 100 (full rollout) if not specified.
        
    Environment Variables:
        ATLASSIAN_ADF_ROLLOUT_PERCENTAGE: Percentage (0-100) for gradual rollout
    """
    percentage_str = os.getenv("ATLASSIAN_ADF_ROLLOUT_PERCENTAGE", "100")
    try:
        percentage = int(percentage_str)
        # Clamp to valid range
        return max(0, min(100, percentage))
    except ValueError:
        # Invalid value, default to full rollout
        return 100


def is_adf_rollout_enabled_for_user(user_id: str | None = None) -> bool:
    """Check if ADF format should be enabled for a specific user.
    
    Supports multiple rollout strategies:
    1. Percentage-based rollout using hash of user ID
    2. User allowlist/blocklist
    3. Global enable/disable flags
    
    Args:
        user_id: User identifier for hash-based percentage rollout
        
    Returns:
        True if ADF should be enabled for this user, False otherwise
        
    Environment Variables:
        ATLASSIAN_ADF_ROLLOUT_PERCENTAGE: Percentage (0-100) for gradual rollout
        ATLASSIAN_ADF_ROLLOUT_USERS: Comma-separated list of user IDs to enable
        ATLASSIAN_ADF_ROLLOUT_EXCLUDE_USERS: Comma-separated list of user IDs to exclude
        ATLASSIAN_DISABLE_ADF: Global disable flag (overrides rollout)
        ATLASSIAN_ENABLE_ADF: Global enable flag (overrides rollout)
    """
    # Check global disable flag first
    if is_env_truthy("ATLASSIAN_DISABLE_ADF"):
        return False
        
    # Check global enable flag 
    if is_env_truthy("ATLASSIAN_ENABLE_ADF"):
        return True
        
    # Check user-specific exclude list
    exclude_users = os.getenv("ATLASSIAN_ADF_ROLLOUT_EXCLUDE_USERS", "")
    if exclude_users and user_id:
        exclude_list = [u.strip() for u in exclude_users.split(",") if u.strip()]
        if user_id in exclude_list:
            return False
            
    # Check user-specific include list (overrides percentage)
    include_users = os.getenv("ATLASSIAN_ADF_ROLLOUT_USERS", "")
    if include_users and user_id:
        include_list = [u.strip() for u in include_users.split(",") if u.strip()]
        if user_id in include_list:
            return True
            
    # Percentage-based rollout
    rollout_percentage = get_adf_rollout_percentage()
    
    # If 0%, disable for everyone not in include list
    if rollout_percentage == 0:
        return False
        
    # If 100%, enable for everyone not in exclude list  
    if rollout_percentage >= 100:
        return True
        
    # Hash-based percentage rollout
    if user_id:
        # Use hash of user_id to determine inclusion
        import hashlib
        user_hash = int(hashlib.md5(user_id.encode()).hexdigest()[:8], 16)
        user_percentage = user_hash % 100
        return user_percentage < rollout_percentage
    else:
        # No user ID provided, use global percentage as probability
        import random
        return random.randint(0, 99) < rollout_percentage
