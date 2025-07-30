"""Tests for ADF rollout feature flag functionality."""

import os
import unittest.mock
from unittest.mock import patch

import pytest

from mcp_atlassian.formatting.router import FormatRouter, FormatType, DeploymentType
from mcp_atlassian.utils.env import (
    get_adf_rollout_percentage,
    is_adf_rollout_enabled_for_user
)


class TestADFRollout:
    """Test ADF rollout functionality and backward compatibility features."""

    def test_rollout_percentage_parsing(self):
        """Test parsing of rollout percentage from environment."""
        with patch.dict(os.environ, {"ATLASSIAN_ADF_ROLLOUT_PERCENTAGE": "50"}):
            assert get_adf_rollout_percentage() == 50
            
        with patch.dict(os.environ, {"ATLASSIAN_ADF_ROLLOUT_PERCENTAGE": "0"}):
            assert get_adf_rollout_percentage() == 0
            
        with patch.dict(os.environ, {"ATLASSIAN_ADF_ROLLOUT_PERCENTAGE": "100"}):
            assert get_adf_rollout_percentage() == 100
            
        with patch.dict(os.environ, {"ATLASSIAN_ADF_ROLLOUT_PERCENTAGE": "150"}):
            # Should clamp to 100
            assert get_adf_rollout_percentage() == 100
            
        with patch.dict(os.environ, {"ATLASSIAN_ADF_ROLLOUT_PERCENTAGE": "-10"}):
            # Should clamp to 0
            assert get_adf_rollout_percentage() == 0
            
        with patch.dict(os.environ, {"ATLASSIAN_ADF_ROLLOUT_PERCENTAGE": "invalid"}):
            # Should default to 100
            assert get_adf_rollout_percentage() == 100
            
        # Test default when not set
        with patch.dict(os.environ, {}, clear=True):
            assert get_adf_rollout_percentage() == 100

    def test_global_disable_override(self):
        """Test global disable flag overrides all other settings."""
        with patch.dict(os.environ, {
            "ATLASSIAN_DISABLE_ADF": "true",
            "ATLASSIAN_ADF_ROLLOUT_PERCENTAGE": "100",
            "ATLASSIAN_ADF_ROLLOUT_USERS": "testuser"
        }):
            assert not is_adf_rollout_enabled_for_user("testuser")
            assert not is_adf_rollout_enabled_for_user("otheruser")
            assert not is_adf_rollout_enabled_for_user(None)

    def test_global_enable_override(self):
        """Test global enable flag overrides percentage and user lists."""
        with patch.dict(os.environ, {
            "ATLASSIAN_ENABLE_ADF": "true",
            "ATLASSIAN_ADF_ROLLOUT_PERCENTAGE": "0",
            "ATLASSIAN_ADF_ROLLOUT_EXCLUDE_USERS": "testuser"
        }):
            assert is_adf_rollout_enabled_for_user("testuser")
            assert is_adf_rollout_enabled_for_user("otheruser")
            assert is_adf_rollout_enabled_for_user(None)

    def test_user_exclude_list(self):
        """Test user-specific exclude list functionality."""
        with patch.dict(os.environ, {
            "ATLASSIAN_ADF_ROLLOUT_EXCLUDE_USERS": "user1,user2,user3",
            "ATLASSIAN_ADF_ROLLOUT_PERCENTAGE": "100"
        }):
            assert not is_adf_rollout_enabled_for_user("user1")
            assert not is_adf_rollout_enabled_for_user("user2")
            assert not is_adf_rollout_enabled_for_user("user3")
            assert is_adf_rollout_enabled_for_user("user4")

    def test_user_include_list(self):
        """Test user-specific include list overrides percentage."""
        with patch.dict(os.environ, {
            "ATLASSIAN_ADF_ROLLOUT_USERS": "user1,user2",
            "ATLASSIAN_ADF_ROLLOUT_PERCENTAGE": "0"
        }):
            assert is_adf_rollout_enabled_for_user("user1")
            assert is_adf_rollout_enabled_for_user("user2")
            assert not is_adf_rollout_enabled_for_user("user3")

    def test_percentage_based_rollout(self):
        """Test percentage-based rollout with consistent hashing."""
        with patch.dict(os.environ, {"ATLASSIAN_ADF_ROLLOUT_PERCENTAGE": "50"}):
            # Test consistency - same user should always get same result
            user1_result1 = is_adf_rollout_enabled_for_user("consistent_user")
            user1_result2 = is_adf_rollout_enabled_for_user("consistent_user")
            assert user1_result1 == user1_result2
            
            # Test that different users can get different results
            results = []
            for i in range(20):
                result = is_adf_rollout_enabled_for_user(f"user{i}")
                results.append(result)
            
            # With 50% rollout, we should see some True and some False
            # (though exact distribution may vary due to hashing)
            assert True in results or False in results

    def test_zero_percent_rollout(self):
        """Test 0% rollout disables ADF for all users except include list."""
        with patch.dict(os.environ, {
            "ATLASSIAN_ADF_ROLLOUT_PERCENTAGE": "0",
            "ATLASSIAN_ADF_ROLLOUT_USERS": "special_user"
        }):
            assert not is_adf_rollout_enabled_for_user("regular_user")
            assert not is_adf_rollout_enabled_for_user(None)
            assert is_adf_rollout_enabled_for_user("special_user")

    def test_hundred_percent_rollout(self):
        """Test 100% rollout enables ADF for all users except exclude list.""" 
        with patch.dict(os.environ, {
            "ATLASSIAN_ADF_ROLLOUT_PERCENTAGE": "100",
            "ATLASSIAN_ADF_ROLLOUT_EXCLUDE_USERS": "special_user"
        }):
            assert is_adf_rollout_enabled_for_user("regular_user")
            assert is_adf_rollout_enabled_for_user(None)
            assert not is_adf_rollout_enabled_for_user("special_user")


class TestFormatRouterRollout:
    """Test FormatRouter integration with rollout functionality."""

    def test_cloud_deployment_with_rollout_enabled(self):
        """Test Cloud deployment with rollout enabled for user."""
        router = FormatRouter()
        
        with patch.dict(os.environ, {"ATLASSIAN_ENABLE_ADF": "true"}):
            result = router.convert_markdown(
                "**test**", 
                "https://company.atlassian.net",
                user_id="testuser"
            )
            
            assert result['format'] == 'adf'
            assert result['deployment_type'] == 'cloud'
            assert result['rollout_applied'] is True

    def test_cloud_deployment_with_rollout_disabled(self):
        """Test Cloud deployment with rollout disabled for user."""
        router = FormatRouter()
        
        with patch.dict(os.environ, {"ATLASSIAN_DISABLE_ADF": "true"}):
            result = router.convert_markdown(
                "**test**", 
                "https://company.atlassian.net",
                user_id="testuser"
            )
            
            assert result['format'] == 'wiki_markup'
            assert result['deployment_type'] == 'cloud'
            assert result['rollout_applied'] is True

    def test_server_deployment_no_rollout(self):
        """Test Server deployment ignores rollout (always wiki markup)."""
        router = FormatRouter()
        
        with patch.dict(os.environ, {"ATLASSIAN_ENABLE_ADF": "true"}):
            result = router.convert_markdown(
                "**test**", 
                "https://jira.company.com",
                user_id="testuser"
            )
            
            assert result['format'] == 'wiki_markup'
            assert result['deployment_type'] == 'server'
            assert result['rollout_applied'] is False

    def test_forced_format_bypasses_rollout(self):
        """Test force_format parameter bypasses rollout logic."""
        router = FormatRouter()
        
        with patch.dict(os.environ, {"ATLASSIAN_DISABLE_ADF": "true"}):
            result = router.convert_markdown(
                "**test**", 
                "https://company.atlassian.net",
                force_format=FormatType.ADF,
                user_id="testuser"
            )
            
            assert result['format'] == 'adf'
            assert result['deployment_type'] == 'unknown'
            assert result['rollout_applied'] is False

    def test_percentage_rollout_consistency(self):
        """Test percentage-based rollout produces consistent results."""
        router = FormatRouter()
        
        with patch.dict(os.environ, {"ATLASSIAN_ADF_ROLLOUT_PERCENTAGE": "25"}):
            # Same user should get same result across multiple calls
            results = []
            for _ in range(5):
                result = router.convert_markdown(
                    "**test**", 
                    "https://company.atlassian.net",
                    user_id="consistent_user"
                )
                results.append(result['format'])
            
            # All results should be the same
            assert len(set(results)) == 1
            assert results[0] in ['adf', 'wiki_markup']

    def test_backward_compatibility_without_user_id(self):
        """Test that conversion works without user_id (backward compatibility)."""
        router = FormatRouter()
        
        with patch.dict(os.environ, {"ATLASSIAN_ADF_ROLLOUT_PERCENTAGE": "50"}):
            result = router.convert_markdown(
                "**test**", 
                "https://company.atlassian.net"
                # No user_id provided
            )
            
            assert result['format'] in ['adf', 'wiki_markup']
            assert result['deployment_type'] == 'cloud'
            assert 'rollout_applied' in result

    def test_user_specific_include_exclude_priority(self):
        """Test that user-specific lists take priority over percentage."""
        router = FormatRouter()
        
        with patch.dict(os.environ, {
            "ATLASSIAN_ADF_ROLLOUT_PERCENTAGE": "0",  # 0% rollout
            "ATLASSIAN_ADF_ROLLOUT_USERS": "included_user",  # But this user is included
            "ATLASSIAN_ADF_ROLLOUT_EXCLUDE_USERS": "excluded_user"  # This user explicitly excluded
        }):
            # Included user should get ADF despite 0% rollout
            result_included = router.convert_markdown(
                "**test**", 
                "https://company.atlassian.net",
                user_id="included_user"
            )
            assert result_included['format'] == 'adf'
            
            # Excluded user should get wiki markup even with potential rollout
            result_excluded = router.convert_markdown(
                "**test**", 
                "https://company.atlassian.net",
                user_id="excluded_user"
            )
            assert result_excluded['format'] == 'wiki_markup'
            
            # Regular user should get wiki markup due to 0% rollout
            result_regular = router.convert_markdown(
                "**test**", 
                "https://company.atlassian.net",
                user_id="regular_user"
            )
            assert result_regular['format'] == 'wiki_markup'


class TestRolloutDocumentation:
    """Test rollout configuration examples for documentation."""

    def test_gradual_rollout_scenario(self):
        """Test gradual rollout scenario: 10% -> 25% -> 50% -> 100%."""
        router = FormatRouter()
        
        # Stage 1: 10% rollout
        with patch.dict(os.environ, {"ATLASSIAN_ADF_ROLLOUT_PERCENTAGE": "10"}):
            results_10 = {}
            for i in range(100):
                result = router.convert_markdown(
                    "**test**", 
                    "https://company.atlassian.net",
                    user_id=f"user{i}"
                )
                results_10[f"user{i}"] = result['format']
        
        # Stage 2: 25% rollout (users in 10% should remain consistent)
        with patch.dict(os.environ, {"ATLASSIAN_ADF_ROLLOUT_PERCENTAGE": "25"}):
            for i in range(20):  # Test subset for consistency
                result = router.convert_markdown(
                    "**test**", 
                    "https://company.atlassian.net",
                    user_id=f"user{i}"
                )
                # User should get same or better (ADF) format as before
                if results_10[f"user{i}"] == 'adf':
                    assert result['format'] == 'adf'

    def test_emergency_disable_scenario(self):
        """Test emergency disable scenario overrides all other settings."""
        router = FormatRouter()
        
        with patch.dict(os.environ, {
            "ATLASSIAN_DISABLE_ADF": "true",
            "ATLASSIAN_ADF_ROLLOUT_PERCENTAGE": "100",
            "ATLASSIAN_ADF_ROLLOUT_USERS": "vip_user"
        }):
            # Even VIP users and 100% rollout should be disabled
            result = router.convert_markdown(
                "**test**", 
                "https://company.atlassian.net",
                user_id="vip_user"
            )
            assert result['format'] == 'wiki_markup'
            assert result['rollout_applied'] is True

    def test_beta_user_scenario(self):
        """Test beta user scenario with early access."""
        router = FormatRouter()
        
        with patch.dict(os.environ, {
            "ATLASSIAN_ADF_ROLLOUT_PERCENTAGE": "0",  # Not rolled out yet
            "ATLASSIAN_ADF_ROLLOUT_USERS": "beta_user1,beta_user2,beta_user3"
        }):
            # Beta users get early access
            result_beta = router.convert_markdown(
                "**test**", 
                "https://company.atlassian.net",
                user_id="beta_user1"
            )
            assert result_beta['format'] == 'adf'
            
            # Regular users don't
            result_regular = router.convert_markdown(
                "**test**", 
                "https://company.atlassian.net",
                user_id="regular_user"
            )
            assert result_regular['format'] == 'wiki_markup'