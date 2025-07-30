# Format Conversion Troubleshooting Guide

**Created:** July 30, 2025  
**Version:** 1.0.0  
**Purpose:** Comprehensive troubleshooting guide for ADF and wiki markup format conversion issues  

## Overview

This guide provides systematic troubleshooting steps for common format conversion issues in the MCP Atlassian server. It covers ADF generation problems, wiki markup conversion errors, deployment detection issues, and performance problems.

## Quick Diagnostic Commands

### System Health Check
```bash
# Test ADF conversion health
python3 -c "
from mcp_atlassian.formatting.router import FormatRouter
router = FormatRouter()
result = router.convert_markdown('**test**', 'https://test.atlassian.net')
print('✓ ADF conversion working' if result['format'] == 'adf' else '✗ ADF conversion failed')
print('✓ No errors' if 'error' not in result else f'✗ Error: {result[\"error\"]}')
"

# Test wiki markup conversion  
python3 -c "
from mcp_atlassian.formatting.router import FormatRouter
router = FormatRouter()
result = router.convert_markdown('**test**', 'https://jira.company.com')
print('✓ Wiki markup working' if result['format'] == 'wiki_markup' else '✗ Wiki markup failed')
"

# Check performance metrics
python3 -c "
from mcp_atlassian.formatting.router import FormatRouter
router = FormatRouter()
metrics = router.get_performance_metrics()
print(f'Error rate: {metrics[\"adf_generator_metrics\"][\"error_rate\"]:.1f}%')
print(f'Avg conversion time: {metrics[\"average_conversion_time\"]*1000:.1f}ms')
print(f'Cache hit rate: {metrics[\"adf_generator_metrics\"][\"cache_hit_rate\"]:.1f}%')
"
```

## Common Issues and Solutions

### 1. ADF Conversion Failures

#### Issue: "ADF conversion failed" errors
**Symptoms:**
- Error messages in logs: "ADF conversion failed"
- Fallback to plain text or wiki markup
- High error rates in performance metrics

**Diagnosis:**
```python
from mcp_atlassian.formatting.adf import ADFGenerator
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

generator = ADFGenerator()

# Test with problematic markdown
test_markdown = """
# Your problematic markdown here
**Bold text** with [link](http://example.com)
"""

try:
    result = generator.markdown_to_adf(test_markdown)
    print("✓ Conversion successful")
    print(f"Result: {result}")
except Exception as e:
    print(f"✗ Conversion failed: {e}")
    
# Check metrics for error patterns
metrics = generator.get_performance_metrics()
print(f"Error rate: {metrics['error_rate']:.1f}%")
print(f"Last error: {metrics['last_error']}")
```

**Solutions:**

1. **HTML Parsing Errors:**
   ```python
   # Check if BeautifulSoup is installed and working
   try:
       from bs4 import BeautifulSoup
       soup = BeautifulSoup("<p>test</p>", 'html.parser')
       print("✓ BeautifulSoup working")
   except ImportError:
       print("✗ Install BeautifulSoup: pip install beautifulsoup4")
   ```

2. **Markdown Parser Issues:**
   ```python
   # Test markdown parser directly
   import markdown
   
   md = markdown.Markdown(extensions=['codehilite', 'tables', 'fenced_code'])
   html = md.convert("**test**")
   print(f"Markdown output: {html}")
   
   if not html or html == "**test**":
       print("✗ Markdown parser not working correctly")
   ```

3. **Memory/Performance Limits:**
   ```python
   # Check if content exceeds limits
   large_content = "# Header\n" + "* Item\n" * 1000  # 1000 list items
   
   generator = ADFGenerator()
   result = generator.markdown_to_adf(large_content)
   
   # Look for truncation indicators
   if "truncated" in str(result):
       print("Content was truncated due to performance limits")
       print("Consider breaking into smaller chunks")
   ```

#### Issue: Invalid ADF JSON structure
**Symptoms:**
- Validation errors when posting to Atlassian APIs
- "Invalid ADF format" responses
- Missing required fields in generated JSON

**Diagnosis:**
```python
from mcp_atlassian.formatting.adf import ADFGenerator

generator = ADFGenerator()
result = generator.markdown_to_adf("**test**")

# Validate ADF structure
is_valid = generator.validate_adf(result)
print(f"ADF valid: {is_valid}")

if not is_valid:
    print("Invalid ADF structure detected")
    print(f"Result: {result}")
    
    # Check required fields
    required = ["version", "type", "content"]
    missing = [field for field in required if field not in result]
    if missing:
        print(f"Missing required fields: {missing}")
```

**Solutions:**

1. **Fix Missing Fields:**
   ```python
   # Ensure all required fields are present
   def fix_adf_structure(adf_json):
       if not isinstance(adf_json, dict):
           return {"version": 1, "type": "doc", "content": []}
           
       # Ensure required fields exist
       adf_json.setdefault("version", 1)
       adf_json.setdefault("type", "doc")
       adf_json.setdefault("content", [])
       
       return adf_json
   ```

2. **Content Validation:**
   ```python
   # Validate content blocks
   def validate_content_blocks(content):
       for block in content:
           if not isinstance(block, dict) or "type" not in block:
               print(f"Invalid content block: {block}")
               return False
       return True
   ```

### 2. Wiki Markup Conversion Issues

#### Issue: Incorrect wiki markup formatting
**Symptoms:**
- Bold/italic formatting not appearing correctly in Jira
- Lists not rendering properly
- Links broken or malformed

**Diagnosis:**
```python
from mcp_atlassian.formatting.router import FormatRouter

router = FormatRouter()

# Test specific formatting patterns
test_cases = [
    "**bold text**",
    "*italic text*", 
    "# Header 1",
    "- List item",
    "[link text](http://example.com)"
]

for test in test_cases:
    result = router.convert_markdown(test, "https://jira.company.com")
    print(f"Input: {test}")
    print(f"Output: {result['content']}")
    print("---")
```

**Solutions:**

1. **Fix Bold/Italic Conflicts:**
   ```python
   # Check for markdown parsing conflicts
   import re
   
   def debug_formatting(text):
       # Test bold pattern
       bold_matches = re.findall(r'\*\*([^*]+)\*\*', text)
       print(f"Bold matches: {bold_matches}")
       
       # Test italic pattern  
       italic_matches = re.findall(r'\*([^*]+)\*', text)
       print(f"Italic matches: {italic_matches}")
       
       # Check for conflicts
       if bold_matches and italic_matches:
           print("Potential bold/italic conflict detected")
   ```

2. **List Formatting Issues:**
   ```python
   # Test list conversion
   list_markdown = """
   - Item 1
   - Item 2
     - Nested item
   - Item 3
   """
   
   result = router.convert_markdown(list_markdown, "https://jira.company.com")
   expected_patterns = ["* Item 1", "* Item 2", "** Nested item"]
   
   for pattern in expected_patterns:
       if pattern not in result['content']:
           print(f"Missing expected pattern: {pattern}")
   ```

### 3. Deployment Detection Problems

#### Issue: Wrong format being used
**Symptoms:**
- Cloud instances getting wiki markup instead of ADF
- Server instances getting ADF instead of wiki markup
- Format doesn't match expected deployment type

**Diagnosis:**
```python
from mcp_atlassian.formatting.router import FormatRouter, DeploymentType

router = FormatRouter()

# Test problematic URLs
test_urls = [
    "https://company.atlassian.net",  # Should be Cloud
    "https://jira.company.com",      # Should be Server
    "https://your-problematic-url.com"
]

for url in test_urls:
    detected = router.detect_deployment_type(url)
    print(f"URL: {url}")
    print(f"Detected: {detected}")
    
    # Test conversion
    result = router.convert_markdown("**test**", url)
    print(f"Format used: {result['format']}")
    print("---")
```

**Solutions:**

1. **Clear Detection Cache:**
   ```python
   # Cache corruption fix
   router = FormatRouter()
   router.clear_cache()
   
   # Retest detection
   detection = router.detect_deployment_type(problematic_url)
   print(f"Detection after cache clear: {detection}")
   ```

2. **Custom Detection Override:**
   ```python
   # Override for specific domains
   from mcp_atlassian.formatting.router import FormatRouter, DeploymentType
   
   class CustomRouter(FormatRouter):
       def detect_deployment_type(self, base_url: str) -> DeploymentType:
           # Custom logic for your environment
           if "your-cloud-domain.com" in base_url:
               return DeploymentType.CLOUD
           elif "your-server-domain.com" in base_url:
               return DeploymentType.SERVER
           return super().detect_deployment_type(base_url)
   ```

3. **Force Format Override:**
   ```python
   # Bypass detection entirely
   from mcp_atlassian.formatting.router import FormatType
   
   result = router.convert_markdown(
       markdown_text,
       base_url,
       force_format=FormatType.ADF  # or FormatType.WIKI_MARKUP
   )
   ```

### 4. Performance Issues

#### Issue: Slow conversion times
**Symptoms:**
- Conversion taking >100ms consistently
- Timeout errors on large documents
- High CPU usage during conversion

**Diagnosis:**
```python
import time
from mcp_atlassian.formatting.router import FormatRouter

router = FormatRouter()

# Benchmark conversion performance
test_content = """
# Large Document Test
""" + "\n".join([f"## Section {i}\n**Bold text** with [link](http://example.com/{i})" for i in range(100)])

start_time = time.time()
result = router.convert_markdown(test_content, "https://test.atlassian.net")
conversion_time = time.time() - start_time

print(f"Conversion time: {conversion_time*1000:.1f}ms")
print(f"Content size: {len(test_content)} characters")
print(f"Performance: {len(test_content)/conversion_time:.0f} chars/second")

# Check metrics
metrics = router.get_performance_metrics()
print(f"Average time: {metrics['average_conversion_time']*1000:.1f}ms")
print(f"Cache hit rate: {metrics['adf_generator_metrics']['cache_hit_rate']:.1f}%")
```

**Solutions:**

1. **Optimize Cache Settings:**
   ```python
   # Increase cache sizes for better performance
   router = FormatRouter(
       cache_ttl=7200,        # 2 hours
       cache_size=500,        # Larger detection cache
       adf_cache_size=1000    # Larger ADF cache
   )
   ```

2. **Break Large Documents:**
   ```python
   def split_large_document(markdown_text, max_size=5000):
       """Split large documents for better performance."""
       if len(markdown_text) <= max_size:
           return [markdown_text]
       
       # Split on double newlines (paragraph boundaries)
       paragraphs = markdown_text.split('\n\n')
       chunks = []
       current_chunk = ""
       
       for paragraph in paragraphs:
           if len(current_chunk + paragraph) > max_size and current_chunk:
               chunks.append(current_chunk.strip())
               current_chunk = paragraph
           else:
               current_chunk += '\n\n' + paragraph if current_chunk else paragraph
       
       if current_chunk:
           chunks.append(current_chunk.strip())
       
       return chunks
   
   # Usage
   large_markdown = "..." # Your large document
   chunks = split_large_document(large_markdown)
   
   results = []
   for chunk in chunks:
       result = router.convert_markdown(chunk, base_url)
       results.append(result)
   ```

3. **Memory Management:**
   ```python
   # Regular cache cleanup
   import gc
   
   def periodic_cleanup(router):
       router.clear_cache()
       router.adf_generator.clear_cache()
       gc.collect()
       print("Cache and memory cleanup completed")
   
   # Call periodically in long-running processes
   periodic_cleanup(router)
   ```

#### Issue: Memory leaks or high memory usage
**Symptoms:**
- Memory usage growing over time
- OutOfMemory errors
- Performance degrading with use

**Diagnosis:**
```python
import psutil
import os

def monitor_memory_usage():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    print(f"Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")
    print(f"Virtual memory: {memory_info.vms / 1024 / 1024:.2f} MB")
    
    return memory_info.rss

# Monitor during conversion
router = FormatRouter()
initial_memory = monitor_memory_usage()

for i in range(100):
    result = router.convert_markdown(f"# Document {i}\n**Content**", "https://test.atlassian.net")
    
    if i % 20 == 0:
        current_memory = monitor_memory_usage()
        growth = (current_memory - initial_memory) / 1024 / 1024
        print(f"Iteration {i}: Memory growth: {growth:.2f} MB")
```

**Solutions:**

1. **Cache Size Limits:**
   ```python
   # Reduce cache sizes if memory is limited
   router = FormatRouter(
       cache_size=50,         # Smaller detection cache
       adf_cache_size=100     # Smaller ADF cache
   )
   ```

2. **Periodic Cleanup:**
   ```python
   conversion_count = 0
   
   def convert_with_cleanup(router, markdown, url):
       global conversion_count
       
       result = router.convert_markdown(markdown, url)
       conversion_count += 1
       
       # Cleanup every 100 conversions
       if conversion_count % 100 == 0:
           router.clear_cache()
           router.adf_generator.clear_cache()
           
       return result
   ```

### 5. Integration Issues

#### Issue: Preprocessor integration failures
**Symptoms:**
- JiraPreprocessor not using ADF for Cloud instances
- ConfluencePreprocessor errors
- Inconsistent format selection

**Diagnosis:**
```python
from mcp_atlassian.preprocessing.jira import JiraPreprocessor

# Test JiraPreprocessor integration
preprocessor = JiraPreprocessor(base_url="https://company.atlassian.net")

# Check if ADF is enabled
print(f"ADF enabled: {getattr(preprocessor, 'enable_adf', 'Not set')}")

# Test conversion
result = preprocessor.markdown_to_jira("**test**")
print(f"Result type: {type(result)}")
print(f"Result: {result}")

# Should be dict for ADF, str for wiki markup
if isinstance(result, dict):
    print("✓ Using ADF format")
elif isinstance(result, str):
    print("✓ Using wiki markup format")
else:
    print("✗ Unexpected result type")
```

**Solutions:**

1. **Enable ADF in Preprocessor:**
   ```python
   # Ensure ADF is enabled for Cloud instances
   from mcp_atlassian.preprocessing.jira import JiraPreprocessor
   
   preprocessor = JiraPreprocessor(
       base_url="https://company.atlassian.net",
       enable_adf=True  # Explicitly enable ADF
   )
   ```

2. **Check Configuration:**
   ```python
   # Verify preprocessor configuration
   from mcp_atlassian.jira.config import JiraConfig
   
   config = JiraConfig(base_url="https://company.atlassian.net")
   print(f"Base URL: {config.base_url}")
   print(f"Enable ADF: {config.enable_adf}")
   print(f"Read only: {config.read_only}")
   ```

## Advanced Troubleshooting

### Debugging with Logging

Enable comprehensive logging for detailed troubleshooting:

```python
import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable specific loggers
logging.getLogger('mcp_atlassian.formatting').setLevel(logging.DEBUG)
logging.getLogger('mcp_atlassian.preprocessing').setLevel(logging.DEBUG)

# Test with logging enabled
from mcp_atlassian.formatting.router import FormatRouter
router = FormatRouter()
result = router.convert_markdown("**test**", "https://test.atlassian.net")
```

### Performance Profiling

Profile conversion performance for optimization:

```python
import cProfile
import pstats
from mcp_atlassian.formatting.router import FormatRouter

def profile_conversion():
    router = FormatRouter()
    
    # Large test document
    test_content = """
    # Performance Test Document
    """ + "\n".join([
        f"## Section {i}\n**Bold** and *italic* text with [link{i}](http://example.com/{i})"
        for i in range(50)
    ])
    
    # Profile the conversion
    profiler = cProfile.Profile()
    profiler.enable()
    
    result = router.convert_markdown(test_content, "https://test.atlassian.net")
    
    profiler.disable()
    
    # Analyze results
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 time-consuming functions

# Run profiling
profile_conversion()
```

### Regression Testing

Create tests to catch conversion regressions:

```python
def test_format_conversion_regression():
    """Test to catch format conversion regressions."""
    router = FormatRouter()
    
    # Test cases with expected outputs
    test_cases = [
        {
            'input': '**bold**',
            'cloud_expected': {'type': 'doc', 'content': [{'type': 'paragraph'}]},
            'server_expected': '*bold*'
        },
        {
            'input': '# Header',
            'cloud_expected': {'type': 'doc', 'content': [{'type': 'heading'}]},
            'server_expected': 'h1.Header'
        }
    ]
    
    for case in test_cases:
        # Test Cloud format
        cloud_result = router.convert_markdown(case['input'], 'https://test.atlassian.net')
        assert cloud_result['format'] == 'adf'
        
        # Test Server format  
        server_result = router.convert_markdown(case['input'], 'https://jira.company.com')
        assert server_result['format'] == 'wiki_markup'
        
        print(f"✓ {case['input']} conversion working correctly")

# Run regression test
test_format_conversion_regression()
```

## Emergency Recovery Procedures

### Complete ADF Failure Recovery

If ADF conversion completely fails:

```bash
# 1. Disable ADF globally
export ATLASSIAN_DISABLE_ADF=true

# 2. Restart service with fallback mode
systemctl restart mcp-atlassian

# 3. Verify fallback working
python3 -c "
from mcp_atlassian.preprocessing.jira import JiraPreprocessor
p = JiraPreprocessor(base_url='https://company.atlassian.net', enable_adf=False)
result = p.markdown_to_jira('**test**')
print('✓ Fallback working' if isinstance(result, str) else '✗ Fallback failed')
"

# 4. Clear all caches
python3 -c "
from mcp_atlassian.formatting.router import FormatRouter
router = FormatRouter()
router.clear_cache()
router.adf_generator.clear_cache()
print('All caches cleared')
"
```

### Performance Emergency Recovery

If performance severely degrades:

```bash
# 1. Reduce cache sizes immediately
export MCP_FORMAT_CACHE_SIZE=10
export MCP_ADF_CACHE_SIZE=25

# 2. Clear existing caches
python3 -c "
from mcp_atlassian.formatting.router import FormatRouter
router = FormatRouter()
router.clear_cache()
router.adf_generator.clear_cache()
router.reset_metrics()
print('Caches cleared and metrics reset')
"

# 3. Test performance recovery
python3 -c "
import time
from mcp_atlassian.formatting.router import FormatRouter
router = FormatRouter(cache_size=10, adf_cache_size=25)
start = time.time()
result = router.convert_markdown('**test**', 'https://test.atlassian.net')
duration = time.time() - start
print(f'Performance test: {duration*1000:.1f}ms')
assert duration < 0.1, 'Performance still degraded'
print('✓ Performance recovered')
"
```

## Support Resources

### Log Analysis Commands

```bash
# Find recent format conversion errors
grep -E "(ADF conversion failed|Failed to convert markdown)" /var/log/mcp-atlassian.log | tail -20

# Check error patterns
grep "conversion failed" /var/log/mcp-atlassian.log | \
  awk '{print $NF}' | sort | uniq -c | sort -nr

# Monitor real-time conversion issues
tail -f /var/log/mcp-atlassian.log | grep -E "(ADF|conversion|format)"
```

### Health Check Script

```bash
#!/bin/bash
# format-health-check.sh

echo "=== Format Conversion Health Check ==="

# Test ADF conversion
python3 -c "
from mcp_atlassian.formatting.router import FormatRouter
router = FormatRouter()
result = router.convert_markdown('**test**', 'https://test.atlassian.net')
print('✓ ADF working' if result['format'] == 'adf' and 'error' not in result else '✗ ADF failed')
"

# Test wiki markup conversion
python3 -c "
from mcp_atlassian.formatting.router import FormatRouter
router = FormatRouter()
result = router.convert_markdown('**test**', 'https://jira.company.com')
print('✓ Wiki markup working' if result['format'] == 'wiki_markup' else '✗ Wiki markup failed')
"

# Check performance
python3 -c "
from mcp_atlassian.formatting.router import FormatRouter
import time
router = FormatRouter()
start = time.time()
router.convert_markdown('# Test\n**Bold** text', 'https://test.atlassian.net')
duration = time.time() - start
print(f'Performance: {duration*1000:.1f}ms', '✓' if duration < 0.1 else '⚠️')
"

echo "=== Health Check Complete ==="
```

---

*This troubleshooting guide provides systematic approaches to diagnose and resolve format conversion issues in the MCP Atlassian server.*