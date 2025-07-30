"""Test performance optimizations in FormatRouter."""

import pytest
import time
from src.mcp_atlassian.formatting.router import FormatRouter, DeploymentType


class TestRouterPerformance:
    """Test that regex patterns are pre-compiled and performance is optimized."""
    
    def test_precompiled_patterns(self):
        """Test that all cloud patterns are pre-compiled."""
        router = FormatRouter()
        
        # Check that patterns are pre-compiled
        assert len(router._cloud_patterns) == 3
        
        # All patterns should be compiled regex objects
        for pattern in router._cloud_patterns:
            assert hasattr(pattern, 'match')
            assert hasattr(pattern, 'pattern')
    
    def test_jira_dev_detection(self):
        """Test that jira-dev.com domains are detected as cloud."""
        router = FormatRouter()
        
        test_urls = [
            "https://test.jira-dev.com",
            "https://mycompany.jira-dev.com", 
            "https://staging.jira-dev.com/browse/TEST-123"
        ]
        
        for url in test_urls:
            deployment_type = router.detect_deployment_type(url)
            assert deployment_type == DeploymentType.CLOUD, f"Failed to detect {url} as cloud"
    
    def test_deployment_detection_performance(self):
        """Test that deployment detection is performant with caching."""
        router = FormatRouter()
        
        # First call - not cached
        start = time.time()
        result1 = router.detect_deployment_type("https://test.atlassian.net")
        first_call_time = time.time() - start
        
        # Second call - should be cached
        start = time.time()
        result2 = router.detect_deployment_type("https://test.atlassian.net")
        cached_call_time = time.time() - start
        
        # Results should be the same
        assert result1 == result2 == DeploymentType.CLOUD
        
        # Cached call should be significantly faster (at least 10x)
        # This is a rough check - caching should make it nearly instant
        assert cached_call_time < first_call_time / 10 or cached_call_time < 0.001
    
    def test_all_cloud_patterns_detected(self):
        """Test that all cloud patterns are properly detected."""
        router = FormatRouter()
        
        test_cases = [
            ("https://test.atlassian.net", DeploymentType.CLOUD),
            ("https://test.atlassian.com", DeploymentType.CLOUD),
            ("https://test.jira-dev.com", DeploymentType.CLOUD),
            ("https://custom.company.com", DeploymentType.SERVER),
            ("https://jira.internal.corp", DeploymentType.SERVER),
        ]
        
        for url, expected_type in test_cases:
            result = router.detect_deployment_type(url)
            assert result == expected_type, f"URL {url} detected as {result}, expected {expected_type}"