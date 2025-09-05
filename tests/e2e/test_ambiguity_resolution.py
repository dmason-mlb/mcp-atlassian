"""
Ambiguity Resolution Tests for Meta-Tools

Tests model ability to correctly select operations and tools when requests
are ambiguous or could map to multiple meta-tools. Validates >95% accuracy
in operation selection and parameter mapping.
"""

import asyncio
from typing import Any, Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

import pytest

from test_model_interactions import LLMSimulator, ConversationContext


class AmbiguityType(Enum):
    """Types of ambiguity that can occur in natural language requests."""
    TOOL_SELECTION = "tool_selection"  # Multiple tools could handle request
    OPERATION_TYPE = "operation_type"  # Unclear if create/update/get/delete
    RESOURCE_TYPE = "resource_type"   # Unclear what resource (issue/page/etc)
    SERVICE_TYPE = "service_type"     # Unclear if Jira/Confluence
    PARAMETER_MAPPING = "parameter_mapping"  # Unclear how to extract parameters


@dataclass
class AmbiguityTestCase:
    """Test case for ambiguity resolution."""
    request: str
    ambiguity_type: AmbiguityType
    expected_tool: str
    expected_operation: str
    expected_service: str
    expected_resource: str
    context: Optional[Dict[str, Any]] = None
    description: str = ""


class AdvancedLLMSimulator(LLMSimulator):
    """
    Extended LLM simulator with advanced disambiguation capabilities.
    
    Adds context-aware reasoning and disambiguation strategies for
    handling ambiguous requests more accurately.
    """
    
    def __init__(self, context: ConversationContext):
        super().__init__(context)
        self.disambiguation_strategies = {
            AmbiguityType.TOOL_SELECTION: self._resolve_tool_ambiguity,
            AmbiguityType.OPERATION_TYPE: self._resolve_operation_ambiguity,
            AmbiguityType.RESOURCE_TYPE: self._resolve_resource_ambiguity,
            AmbiguityType.SERVICE_TYPE: self._resolve_service_ambiguity,
            AmbiguityType.PARAMETER_MAPPING: self._resolve_parameter_ambiguity
        }
    
    def detect_ambiguity(self, request: str) -> List[AmbiguityType]:
        """Detect potential ambiguities in a request."""
        ambiguities = []
        request_lower = request.lower()
        
        # Tool selection ambiguity
        update_indicators = sum(1 for word in ["update", "modify", "change", "edit"] if word in request_lower)
        transition_indicators = sum(1 for word in ["status", "state", "transition", "move"] if word in request_lower)
        if update_indicators > 0 and transition_indicators > 0:
            ambiguities.append(AmbiguityType.TOOL_SELECTION)
        
        # Operation type ambiguity
        operation_words = ["create", "update", "get", "delete", "find", "search", "show"]
        op_count = sum(1 for word in operation_words if word in request_lower)
        if op_count == 0 or op_count > 1:
            ambiguities.append(AmbiguityType.OPERATION_TYPE)
        
        # Resource type ambiguity
        jira_resources = ["issue", "bug", "story", "epic", "task"]
        confluence_resources = ["page", "document", "wiki"]
        if any(jr in request_lower for jr in jira_resources) and any(cr in request_lower for cr in confluence_resources):
            ambiguities.append(AmbiguityType.RESOURCE_TYPE)
        
        # Service type ambiguity
        if "jira" not in request_lower and "confluence" not in request_lower:
            # No explicit service mentioned
            has_jira_hints = any(word in request_lower for word in jira_resources + ["project", "assignee", "priority"])
            has_confluence_hints = any(word in request_lower for word in confluence_resources + ["space", "content"])
            if has_jira_hints and has_confluence_hints:
                ambiguities.append(AmbiguityType.SERVICE_TYPE)
        
        # Parameter mapping ambiguity
        if "it" in request_lower or "that" in request_lower or "this" in request_lower:
            ambiguities.append(AmbiguityType.PARAMETER_MAPPING)
        
        return ambiguities
    
    def resolve_ambiguity(self, request: str, ambiguity_type: AmbiguityType, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Resolve a specific type of ambiguity."""
        strategy = self.disambiguation_strategies.get(ambiguity_type)
        if strategy:
            return strategy(request, context or {})
        return {}
    
    def _resolve_tool_ambiguity(self, request: str, context: Dict) -> Dict[str, Any]:
        """Resolve ambiguity between multiple possible tools."""
        request_lower = request.lower()
        
        # Status/transition vs field update disambiguation
        if "status" in request_lower:
            # Check for transition indicators vs field update indicators
            transition_keywords = ["to", "from", "move", "transition", "workflow"]
            field_keywords = ["set", "change", "update", "modify"]
            
            transition_score = sum(1 for kw in transition_keywords if kw in request_lower)
            field_score = sum(1 for kw in field_keywords if kw in request_lower)
            
            if transition_score > field_score:
                return {"preferred_tool": "workflow_engine", "confidence": 0.8}
            else:
                return {"preferred_tool": "resource_manager", "confidence": 0.7}
        
        # Link vs comment vs field update
        if "add" in request_lower:
            if any(word in request_lower for word in ["link", "relationship", "epic"]):
                return {"preferred_tool": "relationship_manager", "confidence": 0.9}
            elif "comment" in request_lower:
                return {"preferred_tool": "resource_manager", "confidence": 0.95}
            else:
                return {"preferred_tool": "resource_manager", "confidence": 0.6}
        
        return {"preferred_tool": "resource_manager", "confidence": 0.5}
    
    def _resolve_operation_ambiguity(self, request: str, context: Dict) -> Dict[str, Any]:
        """Resolve ambiguity about what operation to perform."""
        request_lower = request.lower()
        
        # Use context clues and verb analysis
        if not any(op in request_lower for op in ["create", "update", "delete", "get", "find", "search"]):
            # No explicit operation verb, infer from context
            if "new" in request_lower or "add" in request_lower:
                return {"operation": "create", "confidence": 0.8}
            elif any(word in request_lower for word in ["show", "display", "view", "see"]):
                return {"operation": "get", "confidence": 0.8}
            elif any(word in request_lower for word in ["change", "modify", "edit"]):
                return {"operation": "update", "confidence": 0.7}
            elif "remove" in request_lower:
                return {"operation": "delete", "confidence": 0.9}
            else:
                # Default based on resource mentions
                if any(word in request_lower for word in ["list", "all", "many"]):
                    return {"operation": "search", "confidence": 0.6}
                else:
                    return {"operation": "get", "confidence": 0.4}
        
        # Multiple operations mentioned, prioritize by context
        operations = []
        for op in ["create", "update", "delete", "get", "find", "search"]:
            if op in request_lower:
                operations.append(op)
        
        if len(operations) == 1:
            return {"operation": operations[0], "confidence": 0.9}
        else:
            # Use sentence structure to determine primary operation
            return {"operation": operations[0], "confidence": 0.6}
    
    def _resolve_resource_ambiguity(self, request: str, context: Dict) -> Dict[str, Any]:
        """Resolve ambiguity about target resource type."""
        request_lower = request.lower()
        
        # Count resource type indicators
        jira_score = sum(1 for word in ["issue", "bug", "story", "epic", "task", "ticket"] if word in request_lower)
        confluence_score = sum(1 for word in ["page", "document", "wiki", "content"] if word in request_lower)
        
        if jira_score > confluence_score:
            # Determine specific Jira resource
            if "epic" in request_lower:
                return {"resource": "epic", "service": "jira", "confidence": 0.9}
            elif any(word in request_lower for word in ["bug", "defect"]):
                return {"resource": "issue", "service": "jira", "confidence": 0.9}
            elif any(word in request_lower for word in ["story", "feature"]):
                return {"resource": "issue", "service": "jira", "confidence": 0.8}
            else:
                return {"resource": "issue", "service": "jira", "confidence": 0.7}
        elif confluence_score > jira_score:
            return {"resource": "page", "service": "confluence", "confidence": 0.8}
        else:
            # Use context from conversation history
            if context.get("current_project"):
                return {"resource": "issue", "service": "jira", "confidence": 0.6}
            elif context.get("current_space"):
                return {"resource": "page", "service": "confluence", "confidence": 0.6}
            else:
                # Default to most common use case
                return {"resource": "issue", "service": "jira", "confidence": 0.4}
    
    def _resolve_service_ambiguity(self, request: str, context: Dict) -> Dict[str, Any]:
        """Resolve ambiguity about which service to use."""
        request_lower = request.lower()
        
        # Explicit service indicators
        if "jira" in request_lower:
            return {"service": "jira", "confidence": 1.0}
        elif "confluence" in request_lower:
            return {"service": "confluence", "confidence": 1.0}
        
        # Resource type indicators
        jira_keywords = ["issue", "bug", "story", "epic", "task", "project", "sprint", "board"]
        confluence_keywords = ["page", "document", "wiki", "space", "content", "documentation"]
        
        jira_score = sum(1 for kw in jira_keywords if kw in request_lower)
        confluence_score = sum(1 for kw in confluence_keywords if kw in request_lower)
        
        if jira_score > confluence_score:
            return {"service": "jira", "confidence": 0.8}
        elif confluence_score > jira_score:
            return {"service": "confluence", "confidence": 0.8}
        
        # Use conversation context
        recent_ops = self.context.previous_operations[-3:] if self.context.previous_operations else []
        jira_usage = sum(1 for op in recent_ops if op.get("service") == "jira")
        confluence_usage = sum(1 for op in recent_ops if op.get("service") == "confluence")
        
        if jira_usage > confluence_usage:
            return {"service": "jira", "confidence": 0.6}
        elif confluence_usage > jira_usage:
            return {"service": "confluence", "confidence": 0.6}
        
        # Default to Jira as it's more commonly used
        return {"service": "jira", "confidence": 0.4}
    
    def _resolve_parameter_ambiguity(self, request: str, context: Dict) -> Dict[str, Any]:
        """Resolve ambiguous parameter references."""
        request_lower = request.lower()
        resolved_params = {}
        
        # Resolve pronouns and references
        if "it" in request_lower or "this" in request_lower or "that" in request_lower:
            # Look for most recent relevant entity
            if self.context.previous_operations:
                last_op = self.context.previous_operations[-1]
                if "result" in last_op:
                    result = last_op["result"]
                    if "key" in result:
                        resolved_params["identifier"] = result["key"]
                        resolved_params["confidence"] = 0.9
                    elif "id" in result:
                        resolved_params["identifier"] = result["id"]
                        resolved_params["confidence"] = 0.9
        
        # Resolve implicit project/space references
        if self.context.current_project and "project" not in request_lower:
            if any(word in request_lower for word in ["issue", "bug", "story"]):
                resolved_params["project"] = self.context.current_project
                resolved_params["project_confidence"] = 0.8
        
        if self.context.current_space and "space" not in request_lower:
            if any(word in request_lower for word in ["page", "document"]):
                resolved_params["space"] = self.context.current_space
                resolved_params["space_confidence"] = 0.8
        
        return resolved_params
    
    def enhanced_parse_request(self, request: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Enhanced parsing with ambiguity resolution."""
        # Start with basic parsing
        intent = self.parse_natural_request(request)
        
        # Detect ambiguities
        ambiguities = self.detect_ambiguity(request)
        
        # Resolve each ambiguity
        for ambiguity_type in ambiguities:
            resolution = self.resolve_ambiguity(request, ambiguity_type, context)
            
            # Apply resolution to intent
            if ambiguity_type == AmbiguityType.TOOL_SELECTION and "preferred_tool" in resolution:
                intent["preferred_tool"] = resolution["preferred_tool"]
                intent["tool_confidence"] = resolution["confidence"]
            
            elif ambiguity_type == AmbiguityType.OPERATION_TYPE and "operation" in resolution:
                intent["operation"] = resolution["operation"]
                intent["operation_confidence"] = resolution["confidence"]
            
            elif ambiguity_type == AmbiguityType.RESOURCE_TYPE:
                if "resource" in resolution:
                    intent["resource"] = resolution["resource"]
                if "service" in resolution:
                    intent["service"] = resolution["service"]
                intent["resource_confidence"] = resolution["confidence"]
            
            elif ambiguity_type == AmbiguityType.SERVICE_TYPE and "service" in resolution:
                intent["service"] = resolution["service"]
                intent["service_confidence"] = resolution["confidence"]
            
            elif ambiguity_type == AmbiguityType.PARAMETER_MAPPING:
                intent["resolved_params"] = resolution
        
        intent["ambiguities"] = [a.value for a in ambiguities]
        return intent


@pytest.mark.e2e
@pytest.mark.ambiguity_resolution
class TestAmbiguityResolution:
    """
    Test suite for ambiguity resolution in meta-tool selection.
    
    Validates that models can correctly disambiguate between similar
    operations and select the appropriate meta-tool and parameters.
    """

    @pytest.fixture
    def conversation_context(self):
        """Provide conversation context with some history."""
        context = ConversationContext()
        context.current_project = "AMBIG"
        context.add_operation({
            "service": "jira",
            "result": {"key": "AMBIG-123", "id": "123456"}
        })
        return context
    
    @pytest.fixture
    def advanced_simulator(self, conversation_context):
        """Provide advanced LLM simulator with disambiguation."""
        return AdvancedLLMSimulator(conversation_context)

    @pytest.mark.parametrize("test_case", [
        AmbiguityTestCase(
            request="Update the status of the issue to In Progress",
            ambiguity_type=AmbiguityType.TOOL_SELECTION,
            expected_tool="workflow_engine",
            expected_operation="transition",
            expected_service="jira",
            expected_resource="issue",
            description="Status update could be field update or workflow transition"
        ),
        AmbiguityTestCase(
            request="Change the summary of the issue",
            ambiguity_type=AmbiguityType.TOOL_SELECTION,
            expected_tool="resource_manager",
            expected_operation="update",
            expected_service="jira",
            expected_resource="issue",
            description="Field update should use resource_manager not workflow_engine"
        ),
        AmbiguityTestCase(
            request="Add a comment to it",
            ambiguity_type=AmbiguityType.PARAMETER_MAPPING,
            expected_tool="resource_manager",
            expected_operation="add",
            expected_service="jira",
            expected_resource="comment",
            context={"last_issue": "AMBIG-123"},
            description="Pronoun 'it' should resolve to last referenced entity"
        ),
        AmbiguityTestCase(
            request="Create a new one in the project",
            ambiguity_type=AmbiguityType.RESOURCE_TYPE,
            expected_tool="resource_manager", 
            expected_operation="create",
            expected_service="jira",
            expected_resource="issue",
            description="'One' should infer resource type from context"
        ),
        AmbiguityTestCase(
            request="Find all the items assigned to john",
            ambiguity_type=AmbiguityType.RESOURCE_TYPE,
            expected_tool="search_engine",
            expected_operation="search",
            expected_service="jira",
            expected_resource="issue",
            description="'Items' should infer issues in Jira context"
        )
    ])
    async def test_specific_ambiguity_resolution(
        self, mcp_client, advanced_simulator, test_case
    ):
        """Test resolution of specific ambiguity types."""
        # Parse request with disambiguation
        intent = advanced_simulator.enhanced_parse_request(
            test_case.request, 
            test_case.context
        )
        
        # Verify ambiguity was detected
        assert test_case.ambiguity_type.value in intent.get("ambiguities", [])
        
        # Verify correct resolution
        if "preferred_tool" in intent:
            selected_tool = intent["preferred_tool"]
        else:
            selected_tool = advanced_simulator.select_meta_tool(intent)
        
        assert selected_tool == test_case.expected_tool, (
            f"Expected tool {test_case.expected_tool}, got {selected_tool} "
            f"for request: '{test_case.request}'"
        )
        
        assert intent["operation"] == test_case.expected_operation
        assert intent["service"] == test_case.expected_service
        
        # Check confidence scores when available
        if "tool_confidence" in intent:
            assert intent["tool_confidence"] >= 0.6, "Tool selection confidence too low"
        if "operation_confidence" in intent:
            assert intent["operation_confidence"] >= 0.6, "Operation confidence too low"

    @pytest.mark.asyncio
    async def test_tool_selection_disambiguation(
        self, mcp_client, advanced_simulator, conversation_context
    ):
        """Test disambiguation between similar meta-tools."""
        ambiguous_requests = [
            # resource_manager vs workflow_engine
            ("Update issue status to Done", "workflow_engine"),
            ("Update issue priority to High", "resource_manager"),
            ("Move issue to In Progress", "workflow_engine"),
            ("Set assignee to john.doe", "resource_manager"),
            
            # resource_manager vs relationship_manager
            ("Add comment to issue", "resource_manager"),
            ("Link issue to epic", "relationship_manager"),
            ("Add epic relationship", "relationship_manager"),
            ("Add worklog entry", "resource_manager"),
            
            # search_engine vs resource_manager
            ("Find issues in project", "search_engine"),
            ("Get issue PROJ-123", "resource_manager"),
            ("Show all open bugs", "search_engine"),
            ("Retrieve specific issue", "resource_manager"),
        ]
        
        correct_selections = 0
        total_tests = len(ambiguous_requests)
        
        for request, expected_tool in ambiguous_requests:
            intent = advanced_simulator.enhanced_parse_request(request)
            
            if "preferred_tool" in intent:
                selected_tool = intent["preferred_tool"]
            else:
                selected_tool = advanced_simulator.select_meta_tool(intent)
            
            if selected_tool == expected_tool:
                correct_selections += 1
            else:
                print(f"MISMATCH: '{request}' -> Expected: {expected_tool}, Got: {selected_tool}")
        
        accuracy = (correct_selections / total_tests) * 100
        assert accuracy >= 85.0, f"Tool selection accuracy: {accuracy}% (target: >85%)"

    @pytest.mark.asyncio
    async def test_context_dependent_resolution(
        self, mcp_client, advanced_simulator, conversation_context
    ):
        """Test that ambiguity resolution uses conversation context."""
        # Set up context with recent Jira activity
        conversation_context.add_operation({
            "service": "jira",
            "tool": "resource_manager",
            "result": {"key": "CONTEXT-456"}
        })
        
        # Ambiguous requests that should use context
        context_tests = [
            ("Update it", {"identifier": "CONTEXT-456", "operation": "update"}),
            ("Add comment", {"service": "jira", "resource": "comment"}),
            ("Create another one", {"service": "jira", "resource": "issue"}),
            ("Link to the epic", {"service": "jira", "tool": "relationship_manager"}),
        ]
        
        for request, expected_resolution in context_tests:
            intent = advanced_simulator.enhanced_parse_request(request)
            
            # Check that context was used appropriately
            if "identifier" in expected_resolution:
                resolved_params = intent.get("resolved_params", {})
                assert "identifier" in resolved_params
                assert resolved_params["identifier"] == expected_resolution["identifier"]
            
            if "service" in expected_resolution:
                assert intent["service"] == expected_resolution["service"]
            
            if "resource" in expected_resolution:
                assert intent["resource"] == expected_resolution["resource"]

    @pytest.mark.asyncio
    async def test_pronoun_resolution(
        self, mcp_client, advanced_simulator, conversation_context
    ):
        """Test resolution of pronouns and implicit references."""
        # Add entities to context
        conversation_context.add_operation({
            "result": {"key": "PRON-789", "type": "issue"}
        })
        conversation_context.add_operation({
            "result": {"id": "page-123", "type": "page"}
        })
        
        pronoun_tests = [
            ("Update it", "PRON-789"),  # Should resolve to last issue
            ("Delete this", "PRON-789"),  # Should resolve to last entity
            ("Comment on that issue", "PRON-789"),  # Should resolve with type hint
        ]
        
        for request, expected_identifier in pronoun_tests:
            intent = advanced_simulator.enhanced_parse_request(request)
            resolved_params = intent.get("resolved_params", {})
            
            if "identifier" in resolved_params:
                assert resolved_params["identifier"] == expected_identifier
                assert resolved_params.get("confidence", 0) >= 0.8

    @pytest.mark.asyncio
    async def test_operation_inference(
        self, mcp_client, advanced_simulator
    ):
        """Test inference of operations from implicit language."""
        inference_tests = [
            # No explicit operation verb
            ("Show me the issue", "get"),
            ("The bug needs fixing", "update"),
            ("Remove this comment", "delete"),
            ("New task for testing", "create"),
            ("All issues in project", "search"),
            
            # Context-dependent inference
            ("Priority should be High", "update"),
            ("Status: In Progress", "update"),
            ("Assignee: john.doe", "update"),
        ]
        
        for request, expected_operation in inference_tests:
            intent = advanced_simulator.enhanced_parse_request(request)
            assert intent["operation"] == expected_operation, (
                f"Request: '{request}' -> Expected: {expected_operation}, "
                f"Got: {intent['operation']}"
            )

    @pytest.mark.asyncio
    async def test_service_inference_accuracy(
        self, mcp_client, advanced_simulator
    ):
        """Test accuracy of service inference when not explicitly stated."""
        service_tests = [
            # Jira indicators
            ("Create issue", "jira"),
            ("Update bug priority", "jira"),
            ("Assign to user", "jira"),
            ("Sprint planning", "jira"),
            ("Project dashboard", "jira"),
            
            # Confluence indicators  
            ("Create documentation", "confluence"),
            ("Update wiki page", "confluence"),
            ("Space content", "confluence"),
            ("Page templates", "confluence"),
            
            # Ambiguous cases (should have reasonable default)
            ("Create new item", "jira"),  # Default to more common service
            ("Update content", "confluence"),  # Content suggests Confluence
        ]
        
        correct_inferences = 0
        total_tests = len(service_tests)
        
        for request, expected_service in service_tests:
            intent = advanced_simulator.enhanced_parse_request(request)
            if intent["service"] == expected_service:
                correct_inferences += 1
            else:
                print(f"Service inference: '{request}' -> Expected: {expected_service}, Got: {intent['service']}")
        
        accuracy = (correct_inferences / total_tests) * 100
        assert accuracy >= 80.0, f"Service inference accuracy: {accuracy}% (target: >80%)"

    @pytest.mark.asyncio
    async def test_confidence_scoring(
        self, mcp_client, advanced_simulator
    ):
        """Test that confidence scores accurately reflect disambiguation quality."""
        confidence_tests = [
            ("Create Jira issue", 0.9),  # High confidence - explicit
            ("Update status to Done", 0.7),  # Medium confidence - some ambiguity
            ("Do something with it", 0.4),  # Low confidence - very ambiguous
            ("Show all items", 0.6),  # Medium confidence - needs inference
        ]
        
        for request, min_expected_confidence in confidence_tests:
            intent = advanced_simulator.enhanced_parse_request(request)
            
            # Check various confidence scores
            confidence_scores = [
                intent.get("tool_confidence", 1.0),
                intent.get("operation_confidence", 1.0), 
                intent.get("service_confidence", 1.0),
                intent.get("resource_confidence", 1.0)
            ]
            
            avg_confidence = sum(score for score in confidence_scores if score is not None) / len(confidence_scores)
            
            assert avg_confidence >= min_expected_confidence, (
                f"Request: '{request}' -> Average confidence: {avg_confidence:.2f}, "
                f"Expected: >={min_expected_confidence}"
            )

    @pytest.mark.asyncio
    async def test_edge_case_disambiguation(
        self, mcp_client, advanced_simulator
    ):
        """Test disambiguation of edge cases and complex scenarios."""
        edge_cases = [
            # Multiple services mentioned
            ("Link Jira issue to Confluence page", "relationship_manager"),
            
            # Conflicting indicators
            ("Update page status", "resource_manager"),  # Page suggests Confluence, status suggests field update
            
            # Nested operations
            ("Create issue and add comment", "resource_manager"),  # Should prioritize primary operation
            
            # Temporal references
            ("Update yesterday's issue", "resource_manager"),  # Should use resource_manager for field update
            
            # Conditional operations
            ("If issue exists, update it", "resource_manager"),  # Should focus on update operation
        ]
        
        for request, expected_tool in edge_cases:
            intent = advanced_simulator.enhanced_parse_request(request)
            selected_tool = intent.get("preferred_tool") or advanced_simulator.select_meta_tool(intent)
            
            assert selected_tool == expected_tool, (
                f"Edge case: '{request}' -> Expected: {expected_tool}, Got: {selected_tool}"
            )

    @pytest.mark.asyncio
    async def test_disambiguation_performance(
        self, mcp_client, advanced_simulator
    ):
        """Test performance of disambiguation process."""
        import time
        
        requests = [
            "Update issue status to In Progress",
            "Create bug for login problem", 
            "Find all issues assigned to me",
            "Add comment to the issue",
            "Link issue to epic"
        ] * 20  # 100 requests total
        
        start_time = time.time()
        
        successful_disambiguations = 0
        for request in requests:
            try:
                intent = advanced_simulator.enhanced_parse_request(request)
                if intent.get("ambiguities"):
                    successful_disambiguations += 1
            except Exception:
                pass
        
        end_time = time.time()
        processing_time = (end_time - start_time) * 1000  # Convert to ms
        
        avg_time_per_request = processing_time / len(requests)
        
        # Performance targets
        assert avg_time_per_request < 50, f"Average disambiguation time: {avg_time_per_request:.2f}ms (target: <50ms)"
        assert successful_disambiguations >= len(requests) * 0.8, f"Disambiguation success rate too low"


@pytest.mark.e2e
@pytest.mark.ambiguity_metrics
class TestAmbiguityMetrics:
    """Test suite for measuring ambiguity resolution metrics."""

    @pytest.mark.asyncio
    async def test_overall_accuracy_benchmark(
        self, mcp_client, advanced_simulator
    ):
        """Comprehensive accuracy benchmark across all ambiguity types."""
        
        test_suite = [
            # Tool selection (40 cases)
            *[("Update status to Done", "workflow_engine")] * 10,
            *[("Update summary field", "resource_manager")] * 10,
            *[("Link to epic", "relationship_manager")] * 10,
            *[("Search for issues", "search_engine")] * 10,
            
            # Operation inference (30 cases)  
            *[("Show the bug", "get")] * 10,
            *[("Remove comment", "delete")] * 10,
            *[("New feature request", "create")] * 10,
            
            # Service inference (30 cases)
            *[("Create issue tracker item", "jira")] * 15,
            *[("Create documentation page", "confluence")] * 15,
        ]
        
        correct_predictions = 0
        total_predictions = len(test_suite)
        
        for request, expected in test_suite:
            intent = advanced_simulator.enhanced_parse_request(request)
            
            # Check different aspects
            if expected in ["workflow_engine", "resource_manager", "relationship_manager", "search_engine"]:
                # Tool selection test
                selected_tool = intent.get("preferred_tool") or advanced_simulator.select_meta_tool(intent)
                if selected_tool == expected:
                    correct_predictions += 1
            elif expected in ["get", "create", "update", "delete"]:
                # Operation test
                if intent["operation"] == expected:
                    correct_predictions += 1
            elif expected in ["jira", "confluence"]:
                # Service test
                if intent["service"] == expected:
                    correct_predictions += 1
        
        overall_accuracy = (correct_predictions / total_predictions) * 100
        
        # Target: >95% overall accuracy
        assert overall_accuracy >= 95.0, (
            f"Overall ambiguity resolution accuracy: {overall_accuracy:.1f}% (target: >95%)"
        )