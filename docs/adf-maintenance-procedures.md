# ADF Maintenance Procedures

**Created:** July 29, 2025
**Version:** 1.0.0
**Purpose:** Comprehensive maintenance procedures for ADF (Atlassian Document Format) implementation

## Overview

This document provides maintenance procedures for the ADF implementation in the MCP Atlassian server. These procedures ensure the system remains up-to-date with Atlassian ADF schema changes, performance optimizations, and operational health.

## ADF Schema Updates

### Monitoring Schema Changes

Atlassian periodically updates the ADF specification. Monitor these channels for changes:

1. **Official Documentation**
   - [Atlassian Developer Documentation](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/)
   - [ADF Schema Repository](https://bitbucket.org/atlassian/adf-builder-javascript/src/master/)
   - Atlassian Developer Newsletter

2. **Version Detection**
   ```bash
   # Check current ADF version in implementation
   grep -r "version.*1" src/mcp_atlassian/formatting/adf.py

   # Monitor API responses for schema version updates
   curl -H "Accept: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        "https://your-domain.atlassian.net/rest/api/3/issue/ISSUE-1" | \
        jq '.fields.description.version'
   ```

3. **Community Resources**
   - Atlassian Developer Community Forums
   - GitHub issues in ADF-related repositories

### Schema Update Process

When Atlassian releases ADF schema updates:

#### Phase 1: Assessment (1-2 days)

1. **Review Schema Changes**
   ```bash
   # Create assessment branch
   git checkout -b feature/adf-schema-update-vX.X

   # Document changes
   mkdir -p docs/schema-updates/vX.X
   curl -o docs/schema-updates/vX.X/new-schema.json \
        "https://unpkg.com/@atlaskit/adf-schema@latest/dist/json-schema/v1/full.json"
   ```

2. **Impact Analysis**
   ```python
   # Run schema comparison script
   uv run python3 scripts/compare_adf_schemas.py \
       --old docs/schema-updates/v1.0/schema.json \
       --new docs/schema-updates/vX.X/new-schema.json \
       --output docs/schema-updates/vX.X/impact_analysis.md
   ```

3. **Test Current Implementation**
   ```bash
   # Run comprehensive test suite
   uv run pytest tests/unit/test_adf_generator.py -v
   uv run pytest tests/integration/test_adf_integration_simple.py -v
   uv run pytest tests/integration/test_adf_api_compatibility.py -v
   ```

#### Phase 2: Implementation (3-5 days)

1. **Update Core ADF Generator**
   ```python
   # Update src/mcp_atlassian/formatting/adf.py

   # Add new element types
   def _convert_new_element_type(self, element: Any) -> dict[str, Any]:
       """Convert new element type to ADF format."""
       return {
           "type": "newElementType",
           "attrs": self._extract_attributes(element),
           "content": self._convert_children(element)
       }

   # Update _convert_html_element_to_adf method
   elif tag_name == 'new-element':
       return self._convert_new_element_type(element)
   ```

2. **Update Validation Logic**
   ```python
   # Enhance validate_adf method
   def validate_adf(self, adf_json: dict[str, Any]) -> bool:
       """Enhanced validation for new schema version."""
       # Check version compatibility
       if adf_json.get("version") > self.SUPPORTED_VERSION:
           logger.warning(f"ADF version {adf_json['version']} > supported {self.SUPPORTED_VERSION}")

       # Add new element type validations
       return self._validate_schema_v2(adf_json)
   ```

3. **Update Documentation**
   ```bash
   # Update API documentation
   vim docs/adf-api-documentation.md

   # Add new element examples
   # Update supported element table
   # Document any breaking changes
   ```

4. **Enhance Tests**
   ```bash
   # Add tests for new elements
   vim tests/unit/test_adf_new_elements.py

   # Update regression tests
   vim tests/unit/test_regression_adf.py

   # Add real-world test cases
   vim tests/integration/test_adf_schema_v2.py
   ```

#### Phase 3: Testing (2-3 days)

1. **Comprehensive Testing**
   ```bash
   # Run full test suite
   uv run pytest --cov=src/mcp_atlassian/formatting --cov-report=term-missing

   # Performance regression testing
   uv run python3 scripts/benchmark_adf_performance.py --baseline

   # Real API testing
   uv run pytest tests/integration/test_adf_api_compatibility.py --live-api
   ```

2. **Backward Compatibility Testing**
   ```bash
   # Test against older Atlassian instances
   ATLASSIAN_URL="https://legacy-instance.atlassian.net" \
   uv run pytest tests/integration/test_backward_compatibility.py
   ```

3. **Performance Validation**
   ```python
   # Check performance metrics
   from mcp_atlassian.formatting.router import FormatRouter

   router = FormatRouter()
   metrics = router.get_performance_metrics()

   assert metrics['average_conversion_time'] < 0.1  # <100ms target
   assert metrics['error_rate'] < 1.0  # <1% error rate
   ```

#### Phase 4: Deployment (1 day)

1. **Staging Deployment**
   ```bash
   # Deploy to staging environment
   git push origin feature/adf-schema-update-vX.X

   # Test staging deployment
   curl -X POST https://staging.mcp-atlassian.com/healthz

   # Run integration tests against staging
   STAGING=true uv run pytest tests/integration/
   ```

2. **Production Deployment**
   ```bash
   # Merge to main branch
   git checkout main
   git merge feature/adf-schema-update-vX.X

   # Tag release
   git tag -a "v1.X.0" -m "ADF Schema Update vX.X support"
   git push origin main --tags

   # Deploy to production
   ./scripts/deploy_production.sh
   ```

3. **Post-Deployment Validation**
   ```bash
   # Monitor deployment health
   curl -X GET https://api.mcp-atlassian.com/healthz | jq '.adf_status'

   # Check error rates
   ./scripts/monitor_adf_errors.sh --duration 1h

   # Validate with real instances
   uv run python3 scripts/validate_live_deployment.py
   ```

## Performance Maintenance

### Regular Performance Monitoring

1. **Weekly Performance Review**
   ```bash
   # Generate performance report
   uv run python3 scripts/generate_performance_report.py --week

   # Check cache hit rates
   uv run python3 -c "
   from mcp_atlassian.formatting.router import FormatRouter
   router = FormatRouter()
   metrics = router.get_performance_metrics()
   print(f'Cache hit rate: {metrics[\"detection_cache_hit_rate\"]:.1f}%')
   print(f'ADF cache rate: {metrics[\"adf_generator_metrics\"][\"cache_hit_rate\"]:.1f}%')
   "
   ```

2. **Performance Optimization**
   ```python
   # Analyze slow conversions
   import logging
   logging.basicConfig(level=logging.DEBUG)

   # Enable performance debugging
   from mcp_atlassian.formatting.adf import ADFGenerator
   generator = ADFGenerator()

   # Process large document and monitor
   result = generator.markdown_to_adf(large_markdown_content)
   metrics = generator.get_performance_metrics()

   if metrics['average_conversion_time'] > 0.05:  # >50ms
       print("Performance tuning needed")
   ```

3. **Cache Optimization**
   ```bash
   # Monitor cache effectiveness
   uv run python3 scripts/analyze_cache_patterns.py --period 7d

   # Adjust cache sizes based on usage
   # Edit FormatRouter cache_size parameters
   # Edit ADFGenerator cache_size parameters
   ```

### Memory Management

1. **Memory Usage Monitoring**
   ```python
   # Monitor memory usage over time
   import psutil
   import time

   from mcp_atlassian.formatting.router import FormatRouter

   router = FormatRouter()

   # Process many documents and monitor memory
   process = psutil.Process()
   initial_memory = process.memory_info().rss

   for i in range(1000):
       result = router.convert_markdown(f"# Document {i}\n\n**Content**", "https://test.atlassian.net")
       if i % 100 == 0:
           current_memory = process.memory_info().rss
           print(f"Iteration {i}: Memory usage: {(current_memory - initial_memory) / 1024 / 1024:.2f} MB")
   ```

2. **Cache Management**
   ```python
   # Regular cache cleanup
   from mcp_atlassian.formatting.router import FormatRouter

   router = FormatRouter()

   # Clear caches periodically
   router.clear_cache()  # Deployment detection cache
   router.adf_generator.clear_cache()  # ADF conversion cache

   # Reset metrics for fresh monitoring
   router.reset_metrics()
   ```

3. **Memory Leak Detection**
   ```bash
   # Run memory leak detection
   uv run python3 scripts/detect_memory_leaks.py --duration 1h

   # Use memory profiler for detailed analysis
   pip install memory-profiler
   uv run python3 -m memory_profiler scripts/profile_adf_memory.py
   ```

## Error Monitoring and Resolution

### Error Detection

1. **Automated Error Monitoring**
   ```python
   # Monitor error rates
   from mcp_atlassian.formatting.router import FormatRouter

   router = FormatRouter()
   metrics = router.get_performance_metrics()

   if metrics['adf_generator_metrics']['error_rate'] > 5.0:  # >5% error rate
       print(f"High error rate detected: {metrics['adf_generator_metrics']['error_rate']:.1f}%")
       print(f"Last error: {metrics['last_error']}")

       # Alert system administrators
       # Log detailed error information
       # Trigger automatic fallback mode
   ```

2. **Error Pattern Analysis**
   ```bash
   # Analyze error logs
   grep -E "(ADF conversion failed|Failed to convert markdown)" /var/log/mcp-atlassian.log | \
       tail -100 | \
       python3 scripts/analyze_error_patterns.py

   # Check for common failure modes
   grep -c "Cache error" /var/log/mcp-atlassian.log
   grep -c "Performance limit" /var/log/mcp-atlassian.log
   grep -c "Conversion Error" /var/log/mcp-atlassian.log
   ```

### Error Resolution

1. **Common Error Scenarios**

   **Cache Errors**
   ```python
   # Resolution: Clear caches and reinitialize
   router = FormatRouter()
   router.clear_cache()
   router.adf_generator.clear_cache()

   # Monitor recovery
   test_result = router.convert_markdown("**test**", "https://test.atlassian.net")
   assert 'error' not in test_result
   ```

   **Performance Limit Errors**
   ```python
   # Resolution: Adjust performance limits
   # Edit src/mcp_atlassian/formatting/adf.py

   # Increase table row limit
   max_rows = 100  # Increased from 50

   # Increase list item limit
   max_items = 200  # Increased from 100

   # Increase text length limit
   if len(text) > 2000:  # Increased from 1000
       text = text[:1997] + "..."
   ```

   **Schema Validation Errors**
   ```python
   # Resolution: Update validation logic
   def validate_adf(self, adf_json: dict[str, Any]) -> bool:
       try:
           # Add more flexible validation
           if not isinstance(adf_json, dict):
               return False

           # Allow newer schema versions with warnings
           if adf_json.get("version", 1) > 1:
               logger.warning(f"Newer ADF version detected: {adf_json['version']}")

           return True  # More permissive validation
       except Exception as e:
           logger.error(f"Validation error: {e}")
           return False
   ```

2. **Emergency Procedures**

   **Complete ADF Failure**
   ```python
   # Emergency fallback to wiki markup
   from mcp_atlassian.preprocessing.jira import JiraPreprocessor

   processor = JiraPreprocessor(base_url="https://company.atlassian.net")

   # Force wiki markup mode
   result = processor.markdown_to_jira(markdown_text, enable_adf=False)
   assert isinstance(result, str)  # Should be wiki markup
   ```

   **Performance Degradation**
   ```python
   # Disable caching temporarily
   from mcp_atlassian.formatting.router import FormatRouter

   # Create router with minimal caching
   router = FormatRouter(cache_ttl=60, cache_size=10)

   # Monitor performance recovery
   import time
   start = time.time()
   result = router.convert_markdown(markdown_text, base_url)
   duration = time.time() - start

   assert duration < 0.1  # Should be fast
   ```

## Deployment Health Monitoring

### Health Check Procedures

1. **Automated Health Checks**
   ```bash
   # Create health check script
   cat > scripts/check_adf_health.sh << 'EOF'
   #!/bin/bash

   # Test ADF conversion
   python3 -c "
   from mcp_atlassian.formatting.router import FormatRouter
   router = FormatRouter()
   result = router.convert_markdown('**test**', 'https://test.atlassian.net')
   assert result['format'] == 'adf'
   assert 'error' not in result
   print('✓ ADF conversion healthy')
   "

   # Test deployment detection
   python3 -c "
   from mcp_atlassian.formatting.router import FormatRouter, DeploymentType
   router = FormatRouter()
   cloud_type = router.detect_deployment_type('https://test.atlassian.net')
   server_type = router.detect_deployment_type('https://jira.company.com')
   assert cloud_type == DeploymentType.CLOUD
   assert server_type == DeploymentType.SERVER
   print('✓ Deployment detection healthy')
   "

   # Test performance
   python3 -c "
   from mcp_atlassian.formatting.router import FormatRouter
   import time
   router = FormatRouter()
   start = time.time()
   router.convert_markdown('# Test\n\n**Bold** with [link](http://example.com)', 'https://test.atlassian.net')
   duration = time.time() - start
   assert duration < 0.1
   print(f'✓ Performance healthy: {duration*1000:.1f}ms')
   "

   echo "All ADF health checks passed"
   EOF

   chmod +x scripts/check_adf_health.sh
   ```

2. **Continuous Monitoring**
   ```bash
   # Add to crontab for regular monitoring
   # */5 * * * * /path/to/mcp-atlassian/scripts/check_adf_health.sh >> /var/log/adf-health.log 2>&1

   # Monitor health check results
   tail -f /var/log/adf-health.log
   ```

3. **Performance Baselines**
   ```python
   # Establish performance baselines
   baseline_metrics = {
       'average_conversion_time': 0.015,  # 15ms
       'cache_hit_rate': 80.0,           # 80%
       'error_rate': 0.0,                # 0%
       'detection_cache_hit_rate': 50.0  # 50%
   }

   # Regular comparison against baselines
   from mcp_atlassian.formatting.router import FormatRouter
   router = FormatRouter()
   current_metrics = router.get_performance_metrics()

   for metric, baseline in baseline_metrics.items():
       current_value = current_metrics.get(metric, 0)
       if metric == 'error_rate' and current_value > baseline * 2:
           print(f"⚠️  {metric}: {current_value:.2f} > baseline {baseline:.2f}")
       elif metric != 'error_rate' and current_value < baseline * 0.8:
           print(f"⚠️  {metric}: {current_value:.2f} < baseline {baseline:.2f}")
       else:
           print(f"✓ {metric}: {current_value:.2f} (baseline: {baseline:.2f})")
   ```

## Documentation Maintenance

### Regular Documentation Updates

1. **Monthly Documentation Review**
   ```bash
   # Check for outdated examples
   grep -r "atlassian.net" docs/ | grep -v "test.atlassian.net"

   # Update performance metrics in documentation
   vim docs/adf-api-documentation.md
   # Update benchmarks table with current metrics

   # Check for broken links
   find docs/ -name "*.md" -exec grep -l "http" {} \; | \
       xargs python3 scripts/check_documentation_links.py
   ```

2. **Version Documentation**
   ```bash
   # Document ADF implementation version
   echo "ADF Implementation Version: $(date +%Y.%m.%d)" > docs/VERSION

   # Update changelog
   vim CHANGELOG.md
   # Add recent changes, performance improvements, bug fixes
   ```

3. **Example Validation**
   ```bash
   # Validate code examples in documentation
   python3 scripts/validate_documentation_examples.py docs/adf-api-documentation.md
   python3 scripts/validate_documentation_examples.py docs/adf-maintenance-procedures.md
   ```

## Troubleshooting Reference

### Common Issues and Solutions

| Issue | Symptoms | Resolution | Prevention |
|-------|----------|------------|------------|
| Cache corruption | Inconsistent results, random errors | `router.clear_cache()` | Regular cache cleanup |
| Memory leaks | Increasing memory usage over time | Restart service, check cache sizes | Monitor memory usage |
| Performance degradation | Slow conversion times | Check cache hit rates, optimize content | Performance monitoring |
| Schema validation failures | ADF validation errors | Update validation logic | Monitor Atlassian updates |
| Deployment detection failures | Wrong format returned | Clear detection cache | Test detection logic |

### Emergency Contacts

- **Development Team**: adf-dev-team@company.com
- **Operations Team**: ops@company.com
- **Atlassian Support**: (for schema-related issues)

### Quick Recovery Commands

```bash
# Emergency ADF disable
export MCP_ATLASSIAN_DISABLE_ADF=true
systemctl restart mcp-atlassian

# Cache reset
python3 -c "
from mcp_atlassian.formatting.router import FormatRouter
router = FormatRouter()
router.clear_cache()
router.adf_generator.clear_cache()
print('Caches cleared')
"

# Performance check
./scripts/check_adf_health.sh

# Fallback to wiki markup
python3 -c "
from mcp_atlassian.preprocessing.jira import JiraPreprocessor
p = JiraPreprocessor(base_url='https://company.atlassian.net')
result = p.markdown_to_jira('**test**', enable_adf=False)
print('Fallback working:', isinstance(result, str))
"
```

---

*This maintenance guide ensures the ADF implementation remains reliable, performant, and up-to-date with Atlassian's evolving standards.*
