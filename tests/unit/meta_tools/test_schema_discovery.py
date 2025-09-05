"""Tests for schema discovery functionality."""

import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from pydantic import BaseModel, Field

from src.mcp_atlassian.meta_tools.schema_discovery import (
    SchemaCache,
    SchemaDiscovery,
    MinimalSchema,
    schema_discovery,
)


class TestSchemaCache:
    """Test cases for SchemaCache with LRU and TTL functionality."""
    
    def test_cache_initialization(self):
        """Test cache initialization with default values."""
        cache = SchemaCache()
        assert cache.max_size == 256
        assert cache.ttl_seconds == 3600
        assert len(cache._cache) == 0
        assert len(cache._access_order) == 0
        assert len(cache._conversation_hints) == 0
    
    def test_cache_initialization_with_custom_values(self):
        """Test cache initialization with custom values."""
        cache = SchemaCache(max_size=128, ttl_seconds=1800)
        assert cache.max_size == 128
        assert cache.ttl_seconds == 1800
    
    def test_cache_put_and_get(self):
        """Test basic put and get operations."""
        cache = SchemaCache()
        
        # Test putting and getting a value
        cache.put("test_key", "test_value")
        assert cache.get("test_key") == "test_value"
        
        # Test conversation hints are updated
        hints = cache.get_conversation_hints()
        assert hints["test_key"] == 1
    
    def test_cache_get_nonexistent_key(self):
        """Test getting a non-existent key returns None."""
        cache = SchemaCache()
        assert cache.get("nonexistent") is None
    
    def test_cache_ttl_expiration(self):
        """Test TTL expiration removes items from cache."""
        cache = SchemaCache(ttl_seconds=1)
        
        # Put a value
        cache.put("test_key", "test_value")
        assert cache.get("test_key") == "test_value"
        
        # Wait for TTL expiration
        time.sleep(1.1)
        
        # Value should be expired and None returned
        assert cache.get("test_key") is None
        assert "test_key" not in cache._cache
        assert "test_key" not in cache._access_order
    
    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = SchemaCache(max_size=2)
        
        # Fill cache to capacity
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        
        # Access key1 to make it most recently used
        cache.get("key1")
        
        # Add a third item, should evict key2 (least recently used)
        cache.put("key3", "value3")
        
        assert cache.get("key1") == "value1"  # Still there
        assert cache.get("key2") is None      # Evicted
        assert cache.get("key3") == "value3"  # Newly added
    
    def test_cache_conversation_hints(self):
        """Test conversation hints tracking and clearing."""
        cache = SchemaCache()
        
        # Add items and access them multiple times
        cache.put("key1", "value1")
        cache.get("key1")
        cache.get("key1")
        
        cache.put("key2", "value2")
        cache.get("key2")
        
        # Check conversation hints
        hints = cache.get_conversation_hints()
        assert hints["key1"] == 2
        assert hints["key2"] == 1
        
        # Clear conversation hints
        cache.clear_conversation_hints()
        hints = cache.get_conversation_hints()
        assert len(hints) == 0
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = SchemaCache(max_size=10, ttl_seconds=7200)
        
        # Add some items
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.get("key1")
        cache.get("key1")
        cache.get("key2")
        
        stats = cache.stats()
        assert stats["size"] == 2
        assert stats["max_size"] == 10
        assert stats["hit_count"] == 3  # Total access count
        assert stats["unique_keys"] == 2
        assert stats["ttl_seconds"] == 7200


class TestMinimalSchema:
    """Test cases for MinimalSchema model."""
    
    def test_minimal_schema_creation(self):
        """Test creating a MinimalSchema instance."""
        schema = MinimalSchema(
            required=["field1", "field2"],
            fields={"field1": "string:Description", "field2": "int:Number"},
            examples={"minimal": {"field1": "value", "field2": 123}},
            cache_key="test_key_v1",
            cache_hint="Valid for conversation"
        )
        
        assert schema.required == ["field1", "field2"]
        assert schema.fields["field1"] == "string:Description"
        assert schema.examples["minimal"]["field1"] == "value"
        assert schema.cache_key == "test_key_v1"


class TestSchemaDiscovery:
    """Test cases for SchemaDiscovery class."""
    
    @pytest.fixture
    def temp_schema_dir(self, tmp_path):
        """Create temporary schema directory for testing."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()
        (schema_dir / "jira").mkdir()
        (schema_dir / "confluence").mkdir()
        
        # Create test schema file
        test_schema = {
            "create": {
                "required": ["field1", "field2"],
                "fields": {
                    "field1": "string:Test field 1",
                    "field2": "string:Test field 2"
                },
                "examples": {
                    "minimal": {"field1": "value1", "field2": "value2"}
                }
            }
        }
        
        with open(schema_dir / "jira" / "test_resource.json", "w") as f:
            json.dump(test_schema, f)
        
        return schema_dir
    
    def test_schema_discovery_initialization(self):
        """Test SchemaDiscovery initialization."""
        discovery = SchemaDiscovery(cache_size=128, cache_ttl=1800)
        
        assert discovery.cache.max_size == 128
        assert discovery.cache.ttl_seconds == 1800
        assert discovery.schema_dir.name == "schemas"
    
    @patch('src.mcp_atlassian.meta_tools.schema_discovery.Path')
    def test_get_resource_schema_from_json(self, mock_path, temp_schema_dir):
        """Test loading schema from JSON file."""
        # Mock the schema directory path
        mock_path.return_value.parent = temp_schema_dir.parent
        
        discovery = SchemaDiscovery()
        discovery.schema_dir = temp_schema_dir
        
        schema = discovery.get_resource_schema("jira", "test_resource", "create")
        
        assert isinstance(schema, MinimalSchema)
        assert schema.required == ["field1", "field2"]
        assert "field1" in schema.fields
        assert "minimal" in schema.examples
        assert schema.cache_key == "jira_test_resource_create_v1"
    
    def test_get_resource_schema_cache_hit(self):
        """Test schema retrieval from cache."""
        discovery = SchemaDiscovery()
        
        # Create mock schema
        mock_schema = MinimalSchema(
            required=["test"],
            fields={"test": "string:test"},
            examples={"minimal": {"test": "value"}},
            cache_key="test_key",
            cache_hint="test"
        )
        
        # Put in cache
        cache_key = "jira_issue_create_v1"
        discovery.cache.put(cache_key, mock_schema)
        
        # Retrieve should hit cache
        result = discovery.get_resource_schema("jira", "issue", "create")
        assert result == mock_schema
        
        # Should increment conversation hints
        hints = discovery.cache.get_conversation_hints()
        assert hints[cache_key] == 1
    
    def test_get_resource_schema_fallback_generation(self):
        """Test fallback schema generation when JSON not found."""
        discovery = SchemaDiscovery()
        
        # Request schema for non-existent resource
        schema = discovery.get_resource_schema("jira", "nonexistent", "create")
        
        assert isinstance(schema, MinimalSchema)
        assert schema.cache_key == "jira_nonexistent_create_v1"
        # Should have fallback fields
        assert "data" in schema.fields
    
    @patch('src.mcp_atlassian.meta_tools.schema_discovery.JiraIssue')
    def test_extract_schema_from_model(self, mock_model):
        """Test schema extraction from Pydantic model."""
        # Mock Pydantic model
        mock_field = MagicMock()
        mock_field.description = "Test field"
        mock_field.annotation = str
        
        mock_model.model_fields = {
            "test_field": mock_field,
            "required_field": mock_field,
        }
        
        discovery = SchemaDiscovery()
        schema = discovery._extract_schema_from_model(mock_model, "create")
        
        assert isinstance(schema, MinimalSchema)
        assert "test_field" in schema.fields
        assert "required_field" in schema.fields
    
    def test_get_capabilities_all_services(self):
        """Test getting capabilities for all services."""
        discovery = SchemaDiscovery()
        capabilities = discovery.get_capabilities()
        
        assert "jira" in capabilities
        assert "confluence" in capabilities
        assert "resources" in capabilities["jira"]
        assert "operations" in capabilities["jira"]
        assert "common_patterns" in capabilities["jira"]
    
    def test_get_capabilities_specific_service(self):
        """Test getting capabilities for specific service."""
        discovery = SchemaDiscovery()
        
        jira_capabilities = discovery.get_capabilities("jira")
        confluence_capabilities = discovery.get_capabilities("confluence")
        
        assert "resources" in jira_capabilities
        assert "issue" in jira_capabilities["resources"]
        assert "page" in confluence_capabilities["resources"]
    
    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        discovery = SchemaDiscovery()
        
        # Add some cached items
        discovery.get_resource_schema("jira", "issue", "create")
        discovery.get_resource_schema("confluence", "page", "create")
        
        stats = discovery.get_cache_stats()
        assert "size" in stats
        assert "hit_count" in stats
        assert stats["size"] >= 2
    
    def test_clear_conversation_hints(self):
        """Test clearing conversation hints."""
        discovery = SchemaDiscovery()
        
        # Generate some cache hits
        discovery.get_resource_schema("jira", "issue", "create")
        discovery.get_resource_schema("jira", "issue", "create")  # Second hit
        
        # Check hints exist
        hints_before = discovery.cache.get_conversation_hints()
        assert len(hints_before) > 0
        
        # Clear hints
        discovery.clear_conversation_hints()
        
        # Check hints are cleared
        hints_after = discovery.cache.get_conversation_hints()
        assert len(hints_after) == 0


class TestSchemaDiscoveryIntegration:
    """Integration tests for schema discovery with real schemas."""
    
    def test_jira_issue_create_schema(self):
        """Test loading real Jira issue create schema."""
        schema = schema_discovery.get_resource_schema("jira", "issue", "create")
        
        assert isinstance(schema, MinimalSchema)
        assert "project_key" in schema.required
        assert "summary" in schema.required  
        assert "issue_type" in schema.required
        assert "minimal" in schema.examples
        assert "complete" in schema.examples
        
        # Verify field descriptions are compact
        for field_desc in schema.fields.values():
            assert ":" in field_desc  # Should have type:description format
    
    def test_confluence_page_create_schema(self):
        """Test loading real Confluence page create schema."""
        schema = schema_discovery.get_resource_schema("confluence", "page", "create")
        
        assert isinstance(schema, MinimalSchema)
        assert "space_id" in schema.required
        assert "title" in schema.required
        assert "body" in schema.required
        assert "minimal" in schema.examples
        
        # Check examples are realistic
        example = schema.examples["minimal"]
        assert "space_id" in example
        assert "title" in example
        assert "body" in example
    
    def test_schema_caching_behavior(self):
        """Test that schemas are properly cached."""
        # First call should cache the schema
        schema1 = schema_discovery.get_resource_schema("jira", "comment", "add")
        
        # Second call should hit cache
        schema2 = schema_discovery.get_resource_schema("jira", "comment", "add")
        
        # Should be the same object (from cache)
        assert schema1 is schema2
        
        # Check conversation hints
        hints = schema_discovery.cache.get_conversation_hints()
        cache_key = "jira_comment_add_v1"
        assert hints[cache_key] == 1  # Only one hit recorded (first was cache miss)
    
    def test_multiple_operations_same_resource(self):
        """Test different operations on same resource have different schemas."""
        create_schema = schema_discovery.get_resource_schema("jira", "issue", "create")
        update_schema = schema_discovery.get_resource_schema("jira", "issue", "update")
        get_schema = schema_discovery.get_resource_schema("jira", "issue", "get")
        
        # Should have different requirements
        assert len(create_schema.required) > len(update_schema.required)
        assert create_schema.required != get_schema.required
        
        # Should have different cache keys
        assert create_schema.cache_key != update_schema.cache_key
        assert update_schema.cache_key != get_schema.cache_key


class TestGlobalSchemaDiscoveryInstance:
    """Test the global schema_discovery instance."""
    
    def test_global_instance_accessible(self):
        """Test that global instance is accessible and functional."""
        assert schema_discovery is not None
        
        # Test it works
        schema = schema_discovery.get_resource_schema("jira", "issue", "create")
        assert isinstance(schema, MinimalSchema)
    
    def test_global_instance_cache_persistence(self):
        """Test that global instance maintains cache between calls."""
        # Make two calls
        schema_discovery.get_resource_schema("jira", "worklog", "add")
        schema_discovery.get_resource_schema("jira", "worklog", "add")
        
        # Check cache has the item
        stats = schema_discovery.get_cache_stats()
        assert stats["size"] >= 1
        
        # Check conversation hints
        hints = schema_discovery.cache.get_conversation_hints()
        assert "jira_worklog_add_v1" in hints


if __name__ == "__main__":
    pytest.main([__file__, "-v"])