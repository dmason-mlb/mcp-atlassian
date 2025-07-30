# ADF Rollout and Backward Compatibility Guide

**Created:** July 30, 2025  
**Version:** 1.0.0  
**Purpose:** Guide for safely rolling out ADF format conversion with backward compatibility controls  

## Overview

The MCP Atlassian server provides comprehensive rollout controls for ADF (Atlassian Document Format) implementation. This allows organizations to gradually migrate from wiki markup to ADF format with fine-grained control over which users and scenarios use the new format.

## Rollout Strategies

### 1. Global Controls

#### Complete Disable
Disable ADF globally, falling back to wiki markup for all Cloud instances:

```bash
export ATLASSIAN_DISABLE_ADF=true
```

#### Complete Enable  
Enable ADF for all Cloud instances (overrides percentage and user controls):

```bash
export ATLASSIAN_ENABLE_ADF=true
```

### 2. Percentage-Based Rollout

Enable ADF for a percentage of users using consistent hash-based selection:

```bash
# Enable ADF for 25% of users
export ATLASSIAN_ADF_ROLLOUT_PERCENTAGE=25

# Enable for 50% of users
export ATLASSIAN_ADF_ROLLOUT_PERCENTAGE=50

# Disable for all users (except include list)
export ATLASSIAN_ADF_ROLLOUT_PERCENTAGE=0

# Enable for all users (except exclude list)  
export ATLASSIAN_ADF_ROLLOUT_PERCENTAGE=100
```

**Key Features:**
- Uses MD5 hash of user ID for consistent selection
- Same user always gets same result across requests
- Gradual rollout maintains user consistency (users in 25% remain in 50%)

### 3. User-Specific Controls

#### Include List (Beta Users)
Always enable ADF for specific users regardless of percentage:

```bash
export ATLASSIAN_ADF_ROLLOUT_USERS="beta_user1,beta_user2,admin@company.com"
```

#### Exclude List (Problem Users)
Always disable ADF for specific users:

```bash  
export ATLASSIAN_ADF_ROLLOUT_EXCLUDE_USERS="problematic_user,legacy_integration"
```

#### Combined Example
```bash
# 10% rollout with beta access and exclusions
export ATLASSIAN_ADF_ROLLOUT_PERCENTAGE=10
export ATLASSIAN_ADF_ROLLOUT_USERS="beta1,beta2,beta3"
export ATLASSIAN_ADF_ROLLOUT_EXCLUDE_USERS="legacy_bot,external_system"
```

## Configuration Priority

The rollout system follows this priority order:

1. **Global Disable** (`ATLASSIAN_DISABLE_ADF`) - Overrides everything
2. **Global Enable** (`ATLASSIAN_ENABLE_ADF`) - Overrides percentage and lists  
3. **User Exclude List** - Blocks specific users
4. **User Include List** - Enables specific users (overrides percentage)
5. **Percentage Rollout** - Hash-based percentage selection
6. **Default Behavior** - 100% rollout if no configuration

## Implementation Examples

### Gradual Rollout Plan

**Phase 1: Beta Testing (Week 1)**
```bash
export ATLASSIAN_ADF_ROLLOUT_PERCENTAGE=0
export ATLASSIAN_ADF_ROLLOUT_USERS="team_lead1,team_lead2,qa_engineer"
```

**Phase 2: Limited Rollout (Week 2)**  
```bash
export ATLASSIAN_ADF_ROLLOUT_PERCENTAGE=10
export ATLASSIAN_ADF_ROLLOUT_USERS="team_lead1,team_lead2,qa_engineer"
export ATLASSIAN_ADF_ROLLOUT_EXCLUDE_USERS="critical_integration"
```

**Phase 3: Expanded Rollout (Week 3)**
```bash
export ATLASSIAN_ADF_ROLLOUT_PERCENTAGE=25
export ATLASSIAN_ADF_ROLLOUT_EXCLUDE_USERS="critical_integration,legacy_system"
```

**Phase 4: Majority Rollout (Week 4)**
```bash
export ATLASSIAN_ADF_ROLLOUT_PERCENTAGE=75
export ATLASSIAN_ADF_ROLLOUT_EXCLUDE_USERS="critical_integration,legacy_system"
```

**Phase 5: Full Rollout (Week 5)**
```bash
export ATLASSIAN_ADF_ROLLOUT_PERCENTAGE=100
export ATLASSIAN_ADF_ROLLOUT_EXCLUDE_USERS="legacy_system"
```

### Emergency Scenarios

#### Emergency Disable
If ADF causes issues, immediately disable for all users:

```bash
export ATLASSIAN_DISABLE_ADF=true
# Restart MCP server to apply immediately
systemctl restart mcp-atlassian
```

#### Rollback to Previous Percentage
```bash
# If 50% rollout causes issues, rollback to 25%
export ATLASSIAN_ADF_ROLLOUT_PERCENTAGE=25
export ATLASSIAN_ADF_ROLLOUT_EXCLUDE_USERS="affected_user1,affected_user2"
```

#### VIP User Protection
```bash
# Ensure critical users never get experimental features
export ATLASSIAN_ADF_ROLLOUT_EXCLUDE_USERS="ceo,board_member,critical_customer"
```

## Programmatic Usage

### Basic Conversion with Rollout
```python
from mcp_atlassian.formatting.router import FormatRouter

router = FormatRouter()

# Convert with user-specific rollout evaluation
result = router.convert_markdown(
    markdown_text="**Bold text** with [link](http://example.com)",
    base_url="https://company.atlassian.net",
    user_id="john.doe@company.com"
)

print(f"Format used: {result['format']}")
print(f"Rollout applied: {result['rollout_applied']}")
```

### Check Rollout Status for User
```python
from mcp_atlassian.utils.env import is_adf_rollout_enabled_for_user

user_id = "test.user@company.com"
adf_enabled = is_adf_rollout_enabled_for_user(user_id)

if adf_enabled:
    print(f"ADF enabled for {user_id}")
else:
    print(f"ADF disabled for {user_id}, will use wiki markup")
```

### Override for Specific Use Cases
```python
from mcp_atlassian.formatting.router import FormatType

# Force ADF regardless of rollout
result = router.convert_markdown(
    markdown_text="**Test**",
    base_url="https://company.atlassian.net",
    force_format=FormatType.ADF,
    user_id="any_user"
)

# Force wiki markup regardless of rollout
result = router.convert_markdown(
    markdown_text="**Test**",
    base_url="https://company.atlassian.net", 
    force_format=FormatType.WIKI_MARKUP,
    user_id="any_user"
)
```

## MCP Integration

### User Token Middleware
When using multi-user MCP deployments, user tokens are automatically extracted:

```python
# MCP server automatically passes user context
result = await jira_tools.create_issue(
    # User ID extracted from token for rollout evaluation
    description="**Bold text**"  # Converted based on user's rollout status
)
```

### HTTP Headers for User Context
For HTTP-based MCP deployments:

```http
POST /tools/jira_create_issue
Authorization: Bearer user_token
X-User-ID: john.doe@company.com

{
    "description": "**Bold text**"
}
```

## Monitoring and Analytics

### Rollout Metrics
Monitor rollout adoption and impact:

```python
from mcp_atlassian.formatting.router import FormatRouter

router = FormatRouter()
metrics = router.get_performance_metrics()

print(f"Total conversions: {metrics['conversions_total']}")
print(f"ADF generator metrics: {metrics['adf_generator_metrics']}")

# Check results for rollout analysis
result = router.convert_markdown("**test**", "https://company.atlassian.net", user_id="test")
if result['rollout_applied']:
    print(f"Rollout decision: {result['format']}")
```

### Log Analysis
Monitor rollout decisions in logs:

```bash
# Check rollout decisions
grep "rollout configuration" /var/log/mcp-atlassian.log

# Monitor ADF adoption rates
grep "ADF enabled for user" /var/log/mcp-atlassian.log | wc -l
grep "ADF disabled for user" /var/log/mcp-atlassian.log | wc -l
```

## Testing Rollout Configuration

### Test Percentage Distribution
```python
def test_rollout_distribution():
    from mcp_atlassian.utils.env import is_adf_rollout_enabled_for_user
    import os
    
    # Set 50% rollout
    os.environ["ATLASSIAN_ADF_ROLLOUT_PERCENTAGE"] = "50"
    
    enabled_count = 0
    total_users = 1000
    
    for i in range(total_users):
        if is_adf_rollout_enabled_for_user(f"user{i}"):
            enabled_count += 1
    
    percentage = (enabled_count / total_users) * 100
    print(f"Actual rollout percentage: {percentage:.1f}%")
    
    # Should be approximately 50% (within reasonable variance)
    assert 40 <= percentage <= 60
```

### Test User Consistency
```python
def test_user_consistency():
    from mcp_atlassian.formatting.router import FormatRouter
    import os
    
    os.environ["ATLASSIAN_ADF_ROLLOUT_PERCENTAGE"] = "30"
    
    router = FormatRouter()
    user_id = "consistent.user@company.com"
    
    # Test multiple conversions for same user
    formats = []
    for _ in range(10):
        result = router.convert_markdown(
            "**test**", 
            "https://company.atlassian.net",
            user_id=user_id
        )
        formats.append(result['format'])
    
    # All should be the same
    assert len(set(formats)) == 1
    print(f"User {user_id} consistently gets: {formats[0]}")
```

## Troubleshooting

### Common Issues

1. **Users Getting Inconsistent Results**
   - Check for typos in user IDs
   - Verify environment variables are properly set
   - Clear FormatRouter cache if needed

2. **Rollout Not Taking Effect**
   - Verify environment variables are set correctly
   - Check priority order (global flags override others)
   - Restart MCP server after environment changes

3. **Percentage Doesn't Match Expected Distribution**
   - Hash-based selection may not distribute exactly
   - Small user samples will show higher variance
   - Use larger sample sizes for testing

### Debug Commands

```python
# Check environment configuration
import os
from mcp_atlassian.utils.env import get_adf_rollout_percentage, is_adf_rollout_enabled_for_user

print("Rollout configuration:")
print(f"Percentage: {get_adf_rollout_percentage()}%")
print(f"Global disable: {os.getenv('ATLASSIAN_DISABLE_ADF', 'false')}")
print(f"Global enable: {os.getenv('ATLASSIAN_ENABLE_ADF', 'false')}")
print(f"Include users: {os.getenv('ATLASSIAN_ADF_ROLLOUT_USERS', 'none')}")
print(f"Exclude users: {os.getenv('ATLASSIAN_ADF_ROLLOUT_EXCLUDE_USERS', 'none')}")

# Test specific user
user_id = "test.user@company.com"
enabled = is_adf_rollout_enabled_for_user(user_id)
print(f"\nUser {user_id}: ADF {'enabled' if enabled else 'disabled'}")
```

## Best Practices

### 1. Planning
- Start with small percentages (5-10%) 
- Use beta users for initial testing
- Plan rollback procedures
- Monitor error rates during rollout

### 2. User Communication
- Notify users about format changes
- Document differences between ADF and wiki markup
- Provide feedback mechanisms

### 3. Technical Implementation
- Test rollout configuration in staging
- Monitor performance impact
- Keep exclude list for critical integrations
- Use consistent user identifiers

### 4. Monitoring
- Track conversion success rates
- Monitor API error rates
- Analyze user feedback
- Measure performance impact

---

*This rollout guide enables safe, controlled migration to ADF format while maintaining backward compatibility and operational flexibility.*