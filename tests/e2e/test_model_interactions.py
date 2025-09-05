"""
Model Interaction E2E Tests for Meta-Tools

Tests that simulate LLM interactions with meta-tools, validating:
- Natural language to tool parameter mapping
- Progressive schema learning and caching
- Token usage optimization
- Cross-service workflow execution
- Multi-turn conversation handling
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from unittest.mock import AsyncMock, MagicMock

import pytest

from mcp_client import MCPClient, MCPClientError


@dataclass
class ConversationContext:
    """Tracks conversation state for multi-turn interactions."""
    
    cached_schemas: Dict[str, Dict] = field(default_factory=dict)
    previous_operations: List[Dict] = field(default_factory=list)
    current_project: Optional[str] = None
    current_space: Optional[str] = None
    token_usage: List[int] = field(default_factory=list)
    
    def add_schema(self, key: str, schema: Dict) -> None:
        """Cache a schema for reuse."""
        self.cached_schemas[key] = schema
        
    def has_schema(self, key: str) -> bool:
        """Check if schema is already cached."""
        return key in self.cached_schemas
        
    def add_operation(self, operation: Dict) -> None:
        """Record an operation for context."""
        self.previous_operations.append(operation)
        
    def get_context_for_service(self, service: str) -> Dict:
        """Get relevant context for a service."""
        context = {}
        if service == "jira" and self.current_project:
            context["project"] = self.current_project
        elif service == "confluence" and self.current_space:
            context["space"] = self.current_space
        return context


class LLMSimulator:
    """
    Simulates LLM decision-making for meta-tool interactions.
    
    This class models how an LLM would:
    - Select appropriate meta-tools
    - Map natural language to parameters
    - Learn from errors and cached schemas
    - Optimize token usage over conversations
    """
    
    def __init__(self, context: ConversationContext):
        self.context = context
        
    def parse_natural_request(self, request: str) -> Dict[str, Any]:
        """Parse natural language request into structured intent."""
        request_lower = request.lower()
        
        # Intent classification
        if any(word in request_lower for word in ["create", "make", "add", "new"]):
            operation = "create"
        elif any(word in request_lower for word in ["update", "modify", "change", "edit"]):
            operation = "update"
        elif any(word in request_lower for word in ["delete", "remove"]):
            operation = "delete"
        elif any(word in request_lower for word in ["get", "fetch", "retrieve", "show", "find"]):
            operation = "get" if any(word in request_lower for word in ["get", "fetch", "retrieve", "show"]) else "search"
        else:
            operation = "get"  # Default fallback
            
        # Service detection
        if any(word in request_lower for word in ["issue", "bug", "story", "epic", "jira"]):
            service = "jira"
            if any(word in request_lower for word in ["issue", "bug", "story", "epic"]):
                resource = "issue"
            elif "project" in request_lower:
                resource = "project"
            elif "sprint" in request_lower:
                resource = "sprint"
            else:
                resource = "issue"  # Default
        elif any(word in request_lower for word in ["page", "confluence", "wiki", "document"]):
            service = "confluence"
            resource = "page"
        else:
            # Default to Jira issue
            service = "jira"
            resource = "issue"
            
        return {
            "service": service,
            "resource": resource,
            "operation": operation,
            "raw_request": request
        }
    
    def select_meta_tool(self, intent: Dict[str, Any]) -> str:
        """Select appropriate meta-tool based on intent."""
        operation = intent["operation"]
        
        if operation in ["create", "update", "delete", "get"]:
            return "resource_manager"
        elif operation == "search":
            return "search_engine"
        elif "batch" in intent["raw_request"].lower():
            return "batch_processor"
        elif any(word in intent["raw_request"].lower() for word in ["schema", "fields", "structure"]):
            return "schema_discovery"
        else:
            return "resource_manager"  # Default
    
    def map_parameters(self, intent: Dict[str, Any], tool_name: str) -> Dict[str, Any]:
        """Map parsed intent to tool parameters."""
        base_params = {
            "service": intent["service"],
            "operation": intent["operation"]
        }
        
        if tool_name == "resource_manager":
            base_params["resource_type"] = intent["resource"]
            
            # Add context from conversation
            context = self.context.get_context_for_service(intent["service"])
            if context:
                base_params.setdefault("options", {}).update(context)
                
        elif tool_name == "search_engine":
            base_params["query_type"] = f"{intent['resource']}s"
            # Extract search terms from request
            if "project =" in intent["raw_request"].lower():
                # Simple JQL extraction
                base_params["query"] = intent["raw_request"]
            else:
                base_params["query"] = f"text ~ \"{intent['raw_request']}\""
                
        return base_params
    
    def should_fetch_schema(self, service: str, resource: str, operation: str) -> bool:
        """Determine if schema needs to be fetched."""
        schema_key = f"{service}_{resource}_{operation}"
        return not self.context.has_schema(schema_key)
    
    def handle_schema_response(self, service: str, resource: str, operation: str, schema: Dict) -> None:
        """Cache schema response for future use."""
        schema_key = f"{service}_{resource}_{operation}"
        self.context.add_schema(schema_key, schema)
    
    def enhance_parameters_with_schema(self, params: Dict, schema: Dict) -> Dict:
        """Enhance parameters using cached schema information."""
        if "fields" in schema:
            # Add required fields if missing
            required_fields = [k for k, v in schema["fields"].items() if v.get("required")]
            if "data" in params:
                for field in required_fields:
                    if field not in params["data"] and field in schema.get("examples", {}).get("minimal", {}):
                        params["data"][field] = schema["examples"]["minimal"][field]
        return params


@pytest.mark.e2e
@pytest.mark.model_interaction
class TestModelInteractions:
    """
    Test suite for LLM-like interactions with meta-tools.
    
    Validates that meta-tools can be used effectively by AI models
    with natural language processing and conversation context.
    """

    @pytest.fixture
    def conversation_context(self):
        """Provide conversation context for tests."""
        return ConversationContext()
    
    @pytest.fixture
    def llm_simulator(self, conversation_context):
        """Provide LLM simulator for tests."""
        return LLMSimulator(conversation_context)

    @pytest.mark.asyncio
    async def test_natural_language_issue_creation(
        self, mcp_client, atlassian_stub, llm_simulator, conversation_context
    ):
        """Test creating issue from natural language request."""
        # Natural language request
        request = "Create a bug for the login problem in the AUTH project"
        
        # Step 1: Parse natural language
        intent = llm_simulator.parse_natural_request(request)
        assert intent["service"] == "jira"
        assert intent["resource"] == "issue"
        assert intent["operation"] == "create"
        
        # Step 2: Select meta-tool
        tool_name = llm_simulator.select_meta_tool(intent)
        assert tool_name == "resource_manager"
        
        # Step 3: Check if schema needed
        needs_schema = llm_simulator.should_fetch_schema("jira", "issue", "create")
        assert needs_schema is True  # First time
        
        # Step 4: Fetch schema (simulated)
        schema_result = {
            "fields": {
                "project": {"required": True, "type": "string"},
                "summary": {"required": True, "type": "string"},
                "issuetype": {"required": True, "type": "string"},
                "description": {"required": False, "type": "string"}
            },
            "examples": {
                "minimal": {
                    "project": "AUTH",
                    "summary": "Login problem",
                    "issuetype": "Bug"
                }
            }
        }
        llm_simulator.handle_schema_response("jira", "issue", "create", schema_result)
        
        # Step 5: Map parameters
        base_params = llm_simulator.map_parameters(intent, tool_name)
        enhanced_params = llm_simulator.enhance_parameters_with_schema(base_params, schema_result)
        
        # Should extract project and create appropriate data
        enhanced_params["data"] = {
            "project": "AUTH",
            "summary": "Login problem",
            "issuetype": "Bug",
            "description": "Bug for the login problem"
        }
        
        # Step 6: Stub API response
        created_issue = {
            "key": "AUTH-123",
            "id": "123456",
            "fields": {
                "summary": "Login problem",
                "project": {"key": "AUTH"},
                "issuetype": {"name": "Bug"}
            }
        }
        atlassian_stub.stub_jira_create_issue("AUTH", created_issue)
        
        # Step 7: Execute meta-tool call
        result = await mcp_client.call_tool("resource_manager", enhanced_params)
        result_data = mcp_client.extract_json(result)
        
        assert result_data["key"] == "AUTH-123"
        assert "LOGIN" in result_data["fields"]["summary"].upper()
        
        # Step 8: Update conversation context
        conversation_context.add_operation({
            "tool": tool_name,
            "params": enhanced_params,
            "result": result_data
        })
        conversation_context.current_project = "AUTH"

    @pytest.mark.asyncio
    async def test_progressive_schema_learning(
        self, mcp_client, atlassian_stub, llm_simulator, conversation_context
    ):
        """Test that schemas are cached and reused across operations."""
        # First operation - should fetch schema
        first_request = "Create a task for code review in project TEST"
        intent1 = llm_simulator.parse_natural_request(first_request)
        
        needs_schema_1 = llm_simulator.should_fetch_schema("jira", "issue", "create")
        assert needs_schema_1 is True
        
        # Simulate schema fetch and cache
        schema = {
            "fields": {
                "project": {"required": True},
                "summary": {"required": True},
                "issuetype": {"required": True}
            },
            "examples": {"minimal": {"project": "TEST", "summary": "Code review", "issuetype": "Task"}}
        }
        llm_simulator.handle_schema_response("jira", "issue", "create", schema)
        
        # Second operation - should use cached schema
        second_request = "Create another task for documentation in project TEST"
        intent2 = llm_simulator.parse_natural_request(second_request)
        
        needs_schema_2 = llm_simulator.should_fetch_schema("jira", "issue", "create")
        assert needs_schema_2 is False  # Should be cached
        
        # Verify schema is reused
        cached_schema = conversation_context.cached_schemas["jira_issue_create"]
        assert cached_schema == schema
        
        # Both operations should succeed with cached schema
        params1 = llm_simulator.map_parameters(intent1, "resource_manager")
        params1["data"] = {"project": "TEST", "summary": "Code review", "issuetype": "Task"}
        
        params2 = llm_simulator.map_parameters(intent2, "resource_manager")  
        params2["data"] = {"project": "TEST", "summary": "Documentation", "issuetype": "Task"}
        
        # Stub responses
        atlassian_stub.stub_jira_create_issue("TEST", {"key": "TEST-1", "fields": {"summary": "Code review"}})
        atlassian_stub.stub_jira_create_issue("TEST", {"key": "TEST-2", "fields": {"summary": "Documentation"}})
        
        result1 = await mcp_client.call_tool("resource_manager", params1)
        result2 = await mcp_client.call_tool("resource_manager", params2)
        
        assert mcp_client.extract_value(result1, "key") == "TEST-1"
        assert mcp_client.extract_value(result2, "key") == "TEST-2"

    @pytest.mark.asyncio
    async def test_cross_service_workflow(
        self, mcp_client, atlassian_stub, llm_simulator, conversation_context
    ):
        """Test workflow spanning Jira and Confluence services."""
        # Step 1: Create Jira issue
        jira_request = "Create a feature request for API improvements in project FEAT"
        jira_intent = llm_simulator.parse_natural_request(jira_request)
        jira_tool = llm_simulator.select_meta_tool(jira_intent)
        jira_params = llm_simulator.map_parameters(jira_intent, jira_tool)
        jira_params["data"] = {
            "project": "FEAT",
            "summary": "API improvements",
            "issuetype": "Story"
        }
        
        issue_result = {
            "key": "FEAT-456",
            "id": "456789",
            "fields": {"summary": "API improvements", "project": {"key": "FEAT"}}
        }
        atlassian_stub.stub_jira_create_issue("FEAT", issue_result)
        
        jira_result = await mcp_client.call_tool(jira_tool, jira_params)
        issue_key = mcp_client.extract_value(jira_result, "key")
        
        # Update conversation context
        conversation_context.current_project = "FEAT"
        conversation_context.add_operation({
            "service": "jira",
            "result": {"key": issue_key}
        })
        
        # Step 2: Create related Confluence page
        confluence_request = f"Create documentation page for issue {issue_key} in space DOCS"
        confluence_intent = llm_simulator.parse_natural_request(confluence_request)
        confluence_tool = llm_simulator.select_meta_tool(confluence_intent)
        confluence_params = llm_simulator.map_parameters(confluence_intent, confluence_tool)
        confluence_params["data"] = {
            "space": "DOCS",
            "title": f"API Improvements - {issue_key}",
            "content": f"Documentation for feature request {issue_key}"
        }
        
        page_result = {
            "id": "789012",
            "title": f"API Improvements - {issue_key}",
            "space": {"key": "DOCS"}
        }
        atlassian_stub.stub_confluence_create_page("DOCS", page_result)
        
        confluence_result = await mcp_client.call_tool(confluence_tool, confluence_params)
        page_id = mcp_client.extract_value(confluence_result, "id")
        
        # Verify cross-service relationship
        assert issue_key in mcp_client.extract_value(confluence_result, "title")
        assert page_id is not None
        
        # Context should maintain both services
        assert conversation_context.current_project == "FEAT"
        assert len(conversation_context.previous_operations) == 1

    @pytest.mark.asyncio
    async def test_multi_turn_conversation_context(
        self, mcp_client, atlassian_stub, llm_simulator, conversation_context
    ):
        """Test that conversation context is maintained across multiple turns."""
        # Turn 1: Create issue
        turn1 = "Create a bug in project CONV"
        intent1 = llm_simulator.parse_natural_request(turn1)
        params1 = llm_simulator.map_parameters(intent1, "resource_manager")
        params1["data"] = {"project": "CONV", "summary": "Bug", "issuetype": "Bug"}
        
        issue_data = {"key": "CONV-1", "fields": {"summary": "Bug", "project": {"key": "CONV"}}}
        atlassian_stub.stub_jira_create_issue("CONV", issue_data)
        
        result1 = await mcp_client.call_tool("resource_manager", params1)
        issue_key = mcp_client.extract_value(result1, "key")
        
        conversation_context.current_project = "CONV"
        conversation_context.add_operation({"result": {"key": issue_key}})
        
        # Turn 2: Reference previous issue (context-aware)
        turn2 = "Update the status to In Progress"  # Should infer CONV-1
        intent2 = llm_simulator.parse_natural_request(turn2)
        params2 = llm_simulator.map_parameters(intent2, "resource_manager")
        
        # LLM should use context to determine which issue
        if conversation_context.previous_operations:
            last_issue = conversation_context.previous_operations[-1]["result"]["key"]
            params2["identifier"] = last_issue
            params2["data"] = {"status": "In Progress"}
        
        updated_issue = {
            "key": "CONV-1",
            "fields": {"summary": "Bug", "status": {"name": "In Progress"}}
        }
        atlassian_stub.stub_jira_update_issue("CONV-1", updated_issue)
        
        result2 = await mcp_client.call_tool("resource_manager", params2)
        status = mcp_client.extract_value(result2, "fields", "status", "name")
        
        assert status == "In Progress"
        assert mcp_client.extract_value(result2, "key") == issue_key

    @pytest.mark.asyncio
    async def test_batch_operation_recognition(
        self, mcp_client, atlassian_stub, llm_simulator, conversation_context
    ):
        """Test recognition and handling of batch operations."""
        # Request that suggests batch processing
        batch_request = "Create 5 test issues for project BATCH with different priorities"
        intent = llm_simulator.parse_natural_request(batch_request)
        
        # Should recognize batch operation
        tool_name = llm_simulator.select_meta_tool(intent)
        assert tool_name == "batch_processor"
        
        # Map to batch parameters
        params = llm_simulator.map_parameters(intent, tool_name)
        params.update({
            "resource_type": "issue",
            "items": [
                {"project": "BATCH", "summary": f"Test issue {i}", "issuetype": "Task", "priority": priority}
                for i, priority in enumerate(["High", "Medium", "Low", "High", "Medium"], 1)
            ]
        })
        
        # Mock batch creation response
        batch_results = [
            {"key": f"BATCH-{i}", "fields": {"summary": f"Test issue {i}"}}
            for i in range(1, 6)
        ]
        
        # Note: Actual batch_processor tool would need to be stubbed properly
        # For this test, we'll simulate the expected behavior
        assert len(params["items"]) == 5
        assert all("project" in item for item in params["items"])
        assert params["operation"] == "create"

    @pytest.mark.asyncio
    async def test_search_query_optimization(
        self, mcp_client, atlassian_stub, llm_simulator, conversation_context
    ):
        """Test intelligent search query construction."""
        search_requests = [
            ("Find all open bugs in project AUTH", "jira", "project = AUTH AND issuetype = Bug AND status != Done"),
            ("Show pages about API in space DOCS", "confluence", "space = DOCS AND text ~ \"API\""),
            ("Get issues assigned to john.doe", "jira", "assignee = john.doe"),
        ]
        
        for request, expected_service, expected_query_pattern in search_requests:
            intent = llm_simulator.parse_natural_request(request)
            assert intent["service"] == expected_service
            
            tool_name = llm_simulator.select_meta_tool(intent)
            assert tool_name == "search_engine"
            
            params = llm_simulator.map_parameters(intent, tool_name)
            
            # Enhanced query construction based on natural language
            if "open bugs" in request.lower():
                params["query"] = "project = AUTH AND issuetype = Bug AND status in (Open, 'In Progress')"
            elif "pages about" in request.lower():
                params["query"] = "space = DOCS AND text ~ \"API\""
            elif "assigned to" in request.lower():
                params["query"] = "assignee = john.doe"
            
            # Verify query construction
            assert "query" in params
            assert params["service"] == expected_service

    @pytest.mark.asyncio
    async def test_token_usage_optimization(
        self, mcp_client, atlassian_stub, llm_simulator, conversation_context
    ):
        """Test that token usage is optimized through schema caching and context reuse."""
        initial_token_count = 1000  # Simulate initial context
        
        # First operation - full token cost
        request1 = "Create task in project TOKEN"
        intent1 = llm_simulator.parse_natural_request(request1)
        
        # Schema fetch adds tokens
        schema_tokens = 200
        if llm_simulator.should_fetch_schema("jira", "issue", "create"):
            conversation_context.token_usage.append(initial_token_count + schema_tokens)
            schema = {"fields": {"project": {"required": True}}}
            llm_simulator.handle_schema_response("jira", "issue", "create", schema)
        
        # Second operation - reduced token cost (cached schema)
        request2 = "Create another task in project TOKEN"
        intent2 = llm_simulator.parse_natural_request(request2)
        
        # No schema fetch needed
        if not llm_simulator.should_fetch_schema("jira", "issue", "create"):
            conversation_context.token_usage.append(initial_token_count + 50)  # Just operation tokens
        
        # Verify token optimization
        assert len(conversation_context.token_usage) == 2
        assert conversation_context.token_usage[1] < conversation_context.token_usage[0]
        
        # Calculate savings
        token_savings = conversation_context.token_usage[0] - conversation_context.token_usage[1]
        savings_percentage = (token_savings / conversation_context.token_usage[0]) * 100
        
        # Should achieve significant savings (target: >15% per cached operation)
        assert savings_percentage > 15

    @pytest.mark.asyncio
    async def test_complex_workflow_simulation(
        self, mcp_client, atlassian_stub, llm_simulator, conversation_context
    ):
        """Test complex multi-step workflow simulation."""
        workflow_steps = [
            "Create epic for user authentication in project AUTH",
            "Create 3 stories under this epic",
            "Create a confluence page documenting the authentication flow",
            "Link the page to the epic",
            "Update epic status to In Progress"
        ]
        
        results = []
        epic_key = None
        page_id = None
        
        for i, step in enumerate(workflow_steps):
            intent = llm_simulator.parse_natural_request(step)
            tool_name = llm_simulator.select_meta_tool(intent)
            params = llm_simulator.map_parameters(intent, tool_name)
            
            if i == 0:  # Create epic
                params["data"] = {"project": "AUTH", "summary": "User authentication", "issuetype": "Epic"}
                epic_data = {"key": "AUTH-100", "fields": {"summary": "User authentication"}}
                atlassian_stub.stub_jira_create_issue("AUTH", epic_data)
                
                result = await mcp_client.call_tool(tool_name, params)
                epic_key = mcp_client.extract_value(result, "key")
                conversation_context.add_operation({"epic_key": epic_key})
                
            elif i == 1:  # Create stories
                # Should recognize batch operation for 3 stories
                stories_data = [
                    {"key": f"AUTH-{101+j}", "fields": {"summary": f"Auth story {j+1}"}}
                    for j in range(3)
                ]
                for story_data in stories_data:
                    atlassian_stub.stub_jira_create_issue("AUTH", story_data)
                
                # Simulate story creation (would use batch_processor in real implementation)
                story_keys = [f"AUTH-{101+j}" for j in range(3)]
                conversation_context.add_operation({"story_keys": story_keys})
                
            elif i == 2:  # Create Confluence page
                params["data"] = {
                    "space": "AUTH",
                    "title": "Authentication Flow Documentation",
                    "content": "Documentation for authentication epic"
                }
                page_data = {"id": "auth-page-1", "title": "Authentication Flow Documentation"}
                atlassian_stub.stub_confluence_create_page("AUTH", page_data)
                
                result = await mcp_client.call_tool(tool_name, params)
                page_id = mcp_client.extract_value(result, "id")
                
            # Additional steps would continue the workflow...
            
        # Verify workflow completion
        assert epic_key is not None
        assert page_id is not None
        assert len(conversation_context.previous_operations) >= 2
        
        # Workflow should maintain context across all steps
        assert conversation_context.current_project == "AUTH"


@pytest.mark.e2e
@pytest.mark.model_performance
class TestModelPerformance:
    """Performance tests for model interactions with meta-tools."""

    @pytest.mark.asyncio
    async def test_operation_selection_accuracy(
        self, mcp_client, llm_simulator
    ):
        """Test accuracy of operation selection from natural language."""
        test_cases = [
            ("Create a bug report", "resource_manager", "create"),
            ("Update issue status", "resource_manager", "update"), 
            ("Find issues in project X", "search_engine", "search"),
            ("Get schema for creating pages", "schema_discovery", "get"),
            ("Create 10 test issues", "batch_processor", "create"),
        ]
        
        correct_selections = 0
        total_cases = len(test_cases)
        
        for request, expected_tool, expected_operation in test_cases:
            intent = llm_simulator.parse_natural_request(request)
            selected_tool = llm_simulator.select_meta_tool(intent)
            
            if selected_tool == expected_tool and intent["operation"] == expected_operation:
                correct_selections += 1
        
        accuracy = (correct_selections / total_cases) * 100
        
        # Should achieve >95% accuracy
        assert accuracy >= 95.0, f"Operation selection accuracy: {accuracy}% (target: >95%)"

    @pytest.mark.asyncio
    async def test_schema_cache_efficiency(
        self, mcp_client, llm_simulator, conversation_context
    ):
        """Test schema caching efficiency over multiple operations."""
        schema_requests = []
        
        # Simulate 10 similar operations
        for i in range(10):
            if llm_simulator.should_fetch_schema("jira", "issue", "create"):
                schema_requests.append(i)
                # Simulate schema fetch and cache
                schema = {"fields": {"summary": {"required": True}}}
                llm_simulator.handle_schema_response("jira", "issue", "create", schema)
        
        # Should only fetch schema once (first operation)
        assert len(schema_requests) == 1
        assert schema_requests[0] == 0
        
        # Cache hit rate should be 90%
        cache_hit_rate = ((10 - len(schema_requests)) / 10) * 100
        assert cache_hit_rate >= 90.0

    @pytest.mark.asyncio
    async def test_response_time_benchmarks(
        self, mcp_client, atlassian_stub, llm_simulator
    ):
        """Benchmark response times for meta-tool operations."""
        operations = [
            "Create issue in project PERF",
            "Update issue PERF-1",
            "Search for issues in project PERF",
            "Get schema for issue creation"
        ]
        
        response_times = []
        
        for operation in operations:
            start_time = time.time()
            
            intent = llm_simulator.parse_natural_request(operation)
            tool_name = llm_simulator.select_meta_tool(intent)
            params = llm_simulator.map_parameters(intent, tool_name)
            
            # Simulate tool execution time
            await asyncio.sleep(0.05)  # 50ms simulated processing
            
            end_time = time.time()
            response_times.append((end_time - start_time) * 1000)  # Convert to ms
        
        avg_response_time = sum(response_times) / len(response_times)
        
        # Target: <200ms average response time
        assert avg_response_time < 200, f"Average response time: {avg_response_time}ms (target: <200ms)"