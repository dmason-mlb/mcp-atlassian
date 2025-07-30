# Deployment Detection and Override Guide

**Created:** July 30, 2025  
**Version:** 1.0.0  
**Purpose:** Comprehensive guide to Atlassian deployment type detection and format override mechanisms  

## Overview

The MCP Atlassian server automatically detects deployment types (Cloud vs Server/Data Center) to select appropriate text formatting (ADF for Cloud, wiki markup for Server/DC). This guide explains the detection mechanisms and provides override options for custom configurations.

## Deployment Detection System

### Automatic Detection Logic

The FormatRouter uses URL pattern matching to determine deployment type:

```python
from mcp_atlassian.formatting.router import FormatRouter, DeploymentType

router = FormatRouter()

# Cloud detection examples
cloud_urls = [
    "https://company.atlassian.net",
    "https://team.atlassian.com", 
    "https://dev.jira-dev.com"
]

# Server/DC detection examples  
server_urls = [
    "https://jira.company.com",
    "https://confluence.internal.org",
    "https://atlassian.mycompany.local"
]

for url in cloud_urls:
    deployment = router.detect_deployment_type(url)
    assert deployment == DeploymentType.CLOUD

for url in server_urls:
    deployment = router.detect_deployment_type(url)
    assert deployment == DeploymentType.SERVER
```

### Detection Patterns

#### Cloud Instance Patterns
- `*.atlassian.net` - Primary Atlassian Cloud domains
- `*.atlassian.com` - Alternative Cloud domains  
- `*.jira-dev.com` - Development/staging Cloud instances

#### Server/DC Instance Patterns
- Custom domains not matching Cloud patterns
- Internal domains (`.local`, `.internal`, `.corp`)
- IP addresses and non-standard hostnames

#### Unknown Patterns
- Invalid URLs or malformed hostnames
- Non-HTTP protocols (FTP, file://, etc.)
- Empty or null URLs

### Caching Mechanism

Detection results are cached with TTL for performance:

```python
from mcp_atlassian.formatting.router import FormatRouter

# Configure cache settings
router = FormatRouter(
    cache_ttl=3600,    # 1 hour cache
    cache_size=100     # Max 100 cached results
)

# Check cache statistics
cache_stats = router.get_cache_stats()
print(f"Cache size: {cache_stats['cache_size']}")
print(f"Cache TTL: {cache_stats['cache_ttl']} seconds")
print(f"Cached deployments: {cache_stats['cached_deployments']}")

# Clear cache when needed
router.clear_cache()
```

## Format Override Mechanisms

### 1. Force Format Type

Override automatic detection by specifying format explicitly:

```python
from mcp_atlassian.formatting.router import FormatRouter, FormatType

router = FormatRouter()

# Force ADF even for Server instances
result = router.convert_markdown(
    markdown_text="**Bold text** with [link](http://example.com)",
    base_url="https://jira.company.com",  # Server URL
    force_format=FormatType.ADF           # Force ADF
)

assert result['format'] == 'adf'
assert result['deployment_type'] == 'unknown'  # Detection bypassed

# Force wiki markup even for Cloud instances  
result = router.convert_markdown(
    markdown_text="**Bold text** with [link](http://example.com)",
    base_url="https://company.atlassian.net",    # Cloud URL
    force_format=FormatType.WIKI_MARKUP          # Force wiki markup
)

assert result['format'] == 'wiki_markup'
assert result['deployment_type'] == 'unknown'  # Detection bypassed
```

### 2. Environment Variable Overrides

Control format selection globally via environment variables:

```bash
# Force ADF for all instances
export ATLASSIAN_FORCE_ADF=true

# Force wiki markup for all instances  
export ATLASSIAN_FORCE_WIKI_MARKUP=true

# Disable ADF globally (fallback to wiki markup)
export ATLASSIAN_DISABLE_ADF=true

# Custom deployment type override
export ATLASSIAN_DEPLOYMENT_TYPE=server  # or 'cloud', 'datacenter'
```

### 3. Configuration-Based Overrides

Override detection in configuration files:

**JiraConfig Override:**
```python
from mcp_atlassian.jira.config import JiraConfig

config = JiraConfig(
    base_url="https://company.atlassian.net",
    deployment_type_override="server",  # Force Server detection
    enable_adf=False                    # Disable ADF
)

# Will use wiki markup despite Cloud URL
```

**ConfluenceConfig Override:**
```python
from mcp_atlassian.confluence.config import ConfluenceConfig

config = ConfluenceConfig(
    base_url="https://jira.company.com", 
    deployment_type_override="cloud",   # Force Cloud detection
    enable_adf=True                     # Enable ADF
)

# Will use ADF despite Server URL
```

### 4. Runtime Override Methods

Override detection programmatically at runtime:

```python
from mcp_atlassian.formatting.router import FormatRouter, DeploymentType

router = FormatRouter()

# Override deployment detection for specific URL
original_detect = router.detect_deployment_type

def custom_detect(url: str) -> DeploymentType:
    if "special.company.com" in url:
        return DeploymentType.CLOUD  # Treat as Cloud
    return original_detect(url)

router.detect_deployment_type = custom_detect

# Test custom detection
deployment = router.detect_deployment_type("https://special.company.com")
assert deployment == DeploymentType.CLOUD
```

## Advanced Configuration Scenarios

### Hybrid Environments

For organizations with mixed Cloud and Server deployments:

```python
class HybridFormatRouter(FormatRouter):
    """Custom router for hybrid Atlassian environments."""
    
    def __init__(self, cloud_domains: list[str], server_domains: list[str]):
        super().__init__()
        self.cloud_domains = cloud_domains
        self.server_domains = server_domains
    
    def detect_deployment_type(self, base_url: str) -> DeploymentType:
        from urllib.parse import urlparse
        
        hostname = urlparse(base_url.lower()).hostname or ""
        
        # Check explicit Cloud domains
        if any(domain in hostname for domain in self.cloud_domains):
            return DeploymentType.CLOUD
            
        # Check explicit Server domains  
        if any(domain in hostname for domain in self.server_domains):
            return DeploymentType.SERVER
            
        # Fallback to default detection
        return super().detect_deployment_type(base_url)

# Usage
router = HybridFormatRouter(
    cloud_domains=["atlassian.net", "cloud.company.com"],
    server_domains=["jira.company.com", "confluence.internal"]
)
```

### Migration Support

Support instances during Cloud migration:

```python
from datetime import datetime, timedelta

class MigrationAwareRouter(FormatRouter):
    """Router that handles Cloud migration scenarios."""
    
    def __init__(self, migration_domains: dict[str, datetime]):
        super().__init__()
        self.migration_domains = migration_domains  # domain -> cutover_date
    
    def detect_deployment_type(self, base_url: str) -> DeploymentType:
        from urllib.parse import urlparse
        
        hostname = urlparse(base_url.lower()).hostname or ""
        
        # Check if domain is in migration
        for domain, cutover_date in self.migration_domains.items():
            if domain in hostname:
                if datetime.now() >= cutover_date:
                    return DeploymentType.CLOUD  # Post-migration
                else:
                    return DeploymentType.SERVER  # Pre-migration
        
        # Standard detection for other domains
        return super().detect_deployment_type(base_url)

# Usage - company.atlassian.net goes live on specific date
migration_router = MigrationAwareRouter({
    "company.atlassian.net": datetime(2025, 8, 15)  # Cutover date
})
```

### Development Environment Overrides

Different behavior for development vs production:

```python
import os
from mcp_atlassian.formatting.router import FormatRouter, DeploymentType

class DevelopmentRouter(FormatRouter):
    """Router with development-specific overrides."""
    
    def detect_deployment_type(self, base_url: str) -> DeploymentType:
        # Development environment overrides
        if os.getenv("ENVIRONMENT") == "development":
            # Force specific deployment type for testing
            override = os.getenv("DEV_DEPLOYMENT_TYPE")
            if override == "cloud":
                return DeploymentType.CLOUD
            elif override == "server":
                return DeploymentType.SERVER
        
        # Production uses standard detection
        return super().detect_deployment_type(base_url)

# Development usage
os.environ["ENVIRONMENT"] = "development"
os.environ["DEV_DEPLOYMENT_TYPE"] = "cloud"

router = DevelopmentRouter()
# All URLs will be treated as Cloud in development
```

## Testing Detection Logic

### Unit Testing Custom Detection

```python
import pytest
from mcp_atlassian.formatting.router import FormatRouter, DeploymentType

def test_custom_detection():
    """Test custom deployment detection logic."""
    router = FormatRouter()
    
    # Test cases
    test_cases = [
        ("https://company.atlassian.net", DeploymentType.CLOUD),
        ("https://jira.company.com", DeploymentType.SERVER),
        ("https://invalid-url", DeploymentType.UNKNOWN),
        ("", DeploymentType.UNKNOWN)
    ]
    
    for url, expected in test_cases:
        result = router.detect_deployment_type(url)
        assert result == expected, f"Failed for {url}: got {result}, expected {expected}"

def test_override_behavior():
    """Test format override mechanisms."""
    router = FormatRouter()
    
    # Test force format override
    result = router.convert_markdown(
        "**test**", 
        "https://company.atlassian.net",
        force_format=FormatType.WIKI_MARKUP
    )
    
    assert result['format'] == 'wiki_markup'
    assert result['deployment_type'] == 'unknown'
```

### Integration Testing

```python
def test_real_deployment_detection():
    """Test detection against real Atlassian instances."""
    router = FormatRouter()
    
    # Test with real Cloud instance
    cloud_result = router.detect_deployment_type("https://atlassian.atlassian.net")
    assert cloud_result == DeploymentType.CLOUD
    
    # Test cache behavior
    cached_result = router.detect_deployment_type("https://atlassian.atlassian.net")
    assert cached_result == DeploymentType.CLOUD
    
    # Verify cache hit
    metrics = router.get_performance_metrics()
    assert metrics['detections_cached'] > 0
```

## Performance Considerations

### Cache Optimization

```python
# Optimize cache settings for your environment
router = FormatRouter(
    cache_ttl=7200,     # 2 hours for stable environments
    cache_size=500      # Larger cache for high-volume deployments
)

# Monitor cache effectiveness
metrics = router.get_performance_metrics()
hit_rate = metrics['detection_cache_hit_rate']

if hit_rate < 50:  # <50% hit rate
    print("Consider increasing cache size or TTL")
elif hit_rate > 95:  # >95% hit rate  
    print("Cache might be too large, consider reducing size")
```

### Detection Performance

```python
import time

# Benchmark detection performance
router = FormatRouter()

start_time = time.time()
for _ in range(1000):
    router.detect_deployment_type("https://company.atlassian.net")
end_time = time.time()

avg_time = (end_time - start_time) / 1000
print(f"Average detection time: {avg_time*1000:.2f}ms")

# Target: <1ms per detection with cache
assert avg_time < 0.001
```

## Troubleshooting Detection Issues

### Common Problems

1. **Incorrect Detection**
   ```python
   # Debug detection logic
   router = FormatRouter()
   
   # Enable debug logging
   import logging
   logging.basicConfig(level=logging.DEBUG)
   
   # Test problematic URL
   result = router.detect_deployment_type("https://problematic.url.com")
   print(f"Detected: {result}")
   
   # Check cache
   cache_stats = router.get_cache_stats()
   print(f"Cached deployments: {cache_stats['cached_deployments']}")
   ```

2. **Cache Issues**
   ```python
   # Clear cache and retry
   router.clear_cache()
   result = router.detect_deployment_type(url)
   
   # Check if cache was the issue
   if result != previous_result:
       print("Cache corruption detected and resolved")
   ```

3. **Performance Issues**
   ```python
   # Monitor detection performance  
   metrics = router.get_performance_metrics()
   
   if metrics['average_detection_time'] > 0.01:  # >10ms
       print("Detection performance degraded")
       print(f"Cache hit rate: {metrics['detection_cache_hit_rate']:.1f}%")
       
       # Possible solutions:
       # - Increase cache size
       # - Clear cache corruption
       # - Check network connectivity
   ```

### Debug Tools

```python
# Debug detection patterns
from mcp_atlassian.formatting.router import FormatRouter
import re

def debug_url_patterns(url: str):
    """Debug which patterns match a URL."""
    router = FormatRouter()
    
    # Test against Cloud patterns
    for pattern in router._cloud_patterns:
        if pattern.match(url):
            print(f"✓ Cloud pattern matched: {pattern.pattern}")
        else:
            print(f"✗ Cloud pattern failed: {pattern.pattern}")
    
    # Test custom patterns
    test_patterns = [
        (r'.*\.internal\..*', "Internal domain"),
        (r'.*\.local$', "Local domain"),
        (r'^\d+\.\d+\.\d+\.\d+', "IP address")
    ]
    
    for pattern_str, description in test_patterns:
        pattern = re.compile(pattern_str)
        if pattern.match(url):
            print(f"✓ {description} matched: {pattern_str}")

# Usage
debug_url_patterns("https://jira.company.internal")
```

## Best Practices

### 1. Consistent Configuration
- Use environment variables for global overrides
- Document custom detection logic clearly  
- Test detection with real instances

### 2. Performance Optimization
- Monitor cache hit rates regularly
- Adjust cache TTL based on environment stability
- Use appropriate cache sizes for your scale

### 3. Maintenance
- Clear caches after infrastructure changes
- Update detection patterns for new domains
- Monitor detection accuracy over time

### 4. Testing
- Include detection tests in CI/CD pipeline
- Test with representative URLs from your environment
- Validate override mechanisms work correctly

---

*This guide ensures reliable deployment detection and provides flexible override mechanisms for complex Atlassian environments.*