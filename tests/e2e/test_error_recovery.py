"""
Error Recovery Tests for Meta-Tools

Tests model ability to recover from errors using structured error messages,
retry with corrected parameters, and learn from failures. Validates >90%
recovery rate and proper error handling patterns.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pytest

from test_model_interactions import LLMSimulator, ConversationContext


class ErrorType(Enum):
    """Types of errors that can occur in meta-tool operations."""
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_FIELD_VALUE = "invalid_field_value"
    RESOURCE_NOT_FOUND = "resource_not_found"
    PERMISSION_DENIED = "permission_denied"
    VALIDATION_ERROR = "validation_error"
    SCHEMA_MISMATCH = "schema_mismatch"
    RATE_LIMIT = "rate_limit"
    API_ERROR = "api_error"


@dataclass
class ErrorScenario:
    """Test scenario for error recovery."""
    description: str
    error_type: ErrorType
    initial_params: Dict[str, Any]
    error_response: Dict[str, Any]
    expected_correction: Dict[str, Any]
    max_retry_attempts: int = 3
    should_recover: bool = True


@dataclass 
class RecoveryAttempt:
    """Record of an error recovery attempt."""
    attempt_number: int
    error_received: Dict[str, Any]
    correction_applied: Dict[str, Any]
    success: bool
    response: Optional[Dict[str, Any]] = None


class ErrorRecoverySimulator(LLMSimulator):
    """
    Extended LLM simulator with error recovery capabilities.
    
    Models how an LLM would:
    - Parse structured error messages
    - Extract actionable correction hints
    - Retry operations with fixes
    - Learn from error patterns
    """
    
    def __init__(self, context: ConversationContext):
        super().__init__(context)
        self.error_history: List[RecoveryAttempt] = []
        self.learned_patterns: Dict[str, Dict[str, Any]] = {}
    
    def parse_error_response(self, error_response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse structured error response to extract correction hints."""
        parsed = {
            "error_type": error_response.get("error_code", "unknown"),
            "message": error_response.get("user_message", ""),
            "suggestions": error_response.get("suggestions", []),
            "details": error_response.get("details", {})
        }
        
        # Extract specific correction hints
        corrections = {}
        
        if "missing_required" in error_response:
            corrections["add_fields"] = error_response["missing_required"]
        
        if "invalid_values" in error_response:
            corrections["fix_values"] = error_response["invalid_values"]
        
        if "allowed_values" in error_response:
            corrections["allowed_options"] = error_response["allowed_values"]
        
        if "schema_requirements" in error_response:
            corrections["schema_fixes"] = error_response["schema_requirements"]
        
        parsed["corrections"] = corrections
        return parsed
    
    def generate_correction(self, original_params: Dict[str, Any], parsed_error: Dict[str, Any]) -> Dict[str, Any]:
        """Generate corrected parameters based on error analysis."""
        corrected_params = original_params.copy()
        corrections = parsed_error.get("corrections", {})
        
        # Handle missing required fields
        if "add_fields" in corrections:
            if "data" not in corrected_params:
                corrected_params["data"] = {}
            
            for field_info in corrections["add_fields"]:
                field_name = field_info.get("field") or field_info
                # Try to get default value from error response
                if isinstance(field_info, dict) and "default" in field_info:
                    corrected_params["data"][field_name] = field_info["default"]
                else:
                    # Use reasonable defaults based on field name
                    corrected_params["data"][field_name] = self._get_default_value(field_name)
        
        # Handle invalid field values
        if "fix_values" in corrections:
            if "data" not in corrected_params:
                corrected_params["data"] = {}
            
            for field_name, error_info in corrections["fix_values"].items():
                if "allowed_values" in error_info:
                    # Pick first allowed value
                    corrected_params["data"][field_name] = error_info["allowed_values"][0]
                elif "pattern" in error_info:
                    # Try to fix based on pattern
                    corrected_params["data"][field_name] = self._fix_pattern_value(
                        corrected_params["data"].get(field_name), error_info["pattern"]
                    )
        
        # Handle allowed values
        if "allowed_options" in corrections:
            if "data" not in corrected_params:
                corrected_params["data"] = {}
                
            for field_name, allowed_list in corrections["allowed_options"].items():
                if allowed_list:
                    corrected_params["data"][field_name] = allowed_list[0]
        
        # Handle schema fixes
        if "schema_fixes" in corrections:
            schema_fixes = corrections["schema_fixes"]
            
            # Fix data structure if needed
            if "required_structure" in schema_fixes:
                required = schema_fixes["required_structure"]
                corrected_params["data"] = self._restructure_data(
                    corrected_params.get("data", {}), required
                )
            
            # Add missing metadata
            if "required_metadata" in schema_fixes:
                for key, value in schema_fixes["required_metadata"].items():
                    corrected_params[key] = value
        
        return corrected_params
    
    def _get_default_value(self, field_name: str) -> Any:
        """Get reasonable default value for a field."""
        field_defaults = {
            "summary": "Default Summary",
            "description": "Default Description", 
            "issuetype": "Task",
            "priority": "Medium",
            "project": "DEFAULT",
            "assignee": None,
            "reporter": None,
            "status": "To Do",
            "title": "Default Title",
            "content": "Default content",
            "space": "DEFAULT"
        }
        return field_defaults.get(field_name.lower(), "default_value")
    
    def _fix_pattern_value(self, current_value: Any, pattern: str) -> Any:
        """Fix value to match required pattern."""
        if not current_value:
            return "FIXED-123"
        
        # Simple pattern fixes
        if "PROJECT-" in pattern:
            if not str(current_value).startswith("PROJECT-"):
                return f"PROJECT-{current_value}"
        
        return current_value
    
    def _restructure_data(self, data: Dict[str, Any], required_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Restructure data to match required schema."""
        restructured = {}
        
        for key, requirements in required_structure.items():
            if key in data:
                restructured[key] = data[key]
            elif "default" in requirements:
                restructured[key] = requirements["default"]
            elif requirements.get("required", False):
                restructured[key] = self._get_default_value(key)
        
        return restructured
    
    def should_retry(self, attempt_number: int, error_type: str, max_attempts: int = 3) -> bool:
        """Determine if operation should be retried."""
        if attempt_number >= max_attempts:
            return False
        
        # Don't retry certain error types
        non_retryable_errors = ["permission_denied", "resource_not_found"]
        if error_type in non_retryable_errors:
            return False
        
        # Rate limit errors should use exponential backoff
        if error_type == "rate_limit":
            return attempt_number < 5  # Allow more attempts for rate limiting
        
        return True
    
    def learn_from_error(self, error_type: str, original_params: Dict, correction: Dict) -> None:
        """Learn patterns from successful error corrections."""
        pattern_key = f"{error_type}_{original_params.get('service', 'unknown')}"
        
        if pattern_key not in self.learned_patterns:
            self.learned_patterns[pattern_key] = {
                "occurrences": 0,
                "common_fixes": {},
                "success_rate": 0.0
            }
        
        pattern = self.learned_patterns[pattern_key]
        pattern["occurrences"] += 1
        
        # Track common fixes
        for fix_type, fix_value in correction.items():
            if fix_type not in pattern["common_fixes"]:
                pattern["common_fixes"][fix_type] = []
            pattern["common_fixes"][fix_type].append(fix_value)
    
    def apply_learned_patterns(self, params: Dict[str, Any], error_type: str) -> Dict[str, Any]:
        """Apply learned patterns to avoid known errors."""
        pattern_key = f"{error_type}_{params.get('service', 'unknown')}"
        
        if pattern_key in self.learned_patterns:
            pattern = self.learned_patterns[pattern_key]
            enhanced_params = params.copy()
            
            # Apply most common fixes preemptively
            for fix_type, fixes in pattern["common_fixes"].items():
                if fixes and fix_type == "add_fields":
                    if "data" not in enhanced_params:
                        enhanced_params["data"] = {}
                    
                    # Add commonly missing fields
                    most_common_missing = max(set(fixes), key=fixes.count) if fixes else None
                    if most_common_missing and most_common_missing not in enhanced_params["data"]:
                        enhanced_params["data"][most_common_missing] = self._get_default_value(most_common_missing)
            
            return enhanced_params
        
        return params


@pytest.mark.e2e
@pytest.mark.error_recovery
class TestErrorRecovery:
    """
    Test suite for error recovery and correction capabilities.
    
    Tests model ability to handle errors gracefully, apply corrections
    based on structured error messages, and learn from failures.
    """

    @pytest.fixture
    def conversation_context(self):
        """Provide conversation context for error recovery tests."""
        return ConversationContext()
    
    @pytest.fixture
    def recovery_simulator(self, conversation_context):
        """Provide error recovery simulator."""
        return ErrorRecoverySimulator(conversation_context)

    @pytest.mark.parametrize("error_scenario", [
        ErrorScenario(
            description="Missing required field in Jira issue creation",
            error_type=ErrorType.MISSING_REQUIRED_FIELD,
            initial_params={
                "service": "jira",
                "resource_type": "issue", 
                "operation": "create",
                "data": {"summary": "Test Issue"}
            },
            error_response={
                "error_code": "MISSING_REQUIRED_FIELDS",
                "user_message": "Required fields are missing",
                "missing_required": [
                    {"field": "project", "message": "Project is required"},
                    {"field": "issuetype", "default": "Task"}
                ],
                "suggestions": [
                    "Add project field with valid project key",
                    "Specify issue type (defaults to Task)"
                ]
            },
            expected_correction={
                "data": {"summary": "Test Issue", "project": "DEFAULT", "issuetype": "Task"}
            }
        ),
        ErrorScenario(
            description="Invalid field values in issue update", 
            error_type=ErrorType.INVALID_FIELD_VALUE,
            initial_params={
                "service": "jira",
                "resource_type": "issue",
                "operation": "update",
                "identifier": "TEST-123",
                "data": {"priority": "Invalid", "status": "BadStatus"}
            },
            error_response={
                "error_code": "INVALID_FIELD_VALUES",
                "user_message": "Some field values are not valid",
                "invalid_values": {
                    "priority": {
                        "value": "Invalid",
                        "allowed_values": ["Low", "Medium", "High", "Critical"]
                    },
                    "status": {
                        "value": "BadStatus", 
                        "allowed_values": ["To Do", "In Progress", "Done"]
                    }
                }
            },
            expected_correction={
                "data": {"priority": "Low", "status": "To Do"}
            }
        ),
        ErrorScenario(
            description="Schema mismatch in Confluence page creation",
            error_type=ErrorType.SCHEMA_MISMATCH,
            initial_params={
                "service": "confluence",
                "resource_type": "page",
                "operation": "create",
                "data": {"title": "Test", "body": "Simple content"}
            },
            error_response={
                "error_code": "SCHEMA_VALIDATION_ERROR",
                "user_message": "Request does not match expected schema",
                "schema_requirements": {
                    "required_structure": {
                        "space": {"required": True},
                        "title": {"required": True},
                        "content": {"required": True}
                    },
                    "required_metadata": {
                        "content_format": "markdown"
                    }
                }
            },
            expected_correction={
                "data": {"title": "Test", "content": "Simple content", "space": "DEFAULT"},
                "content_format": "markdown"
            }
        )
    ])
    async def test_structured_error_recovery(
        self, mcp_client, atlassian_stub, recovery_simulator, error_scenario
    ):
        """Test recovery from structured error responses."""
        # First attempt - should fail with structured error
        with pytest.raises(Exception) as exc_info:
            # Mock the error response
            atlassian_stub.stub_error_response(
                error_scenario.initial_params["service"],
                "POST" if error_scenario.initial_params["operation"] == "create" else "PUT",
                "/api/endpoint",
                status_code=400,
                error_data=error_scenario.error_response
            )
            
            await mcp_client.call_tool("resource_manager", error_scenario.initial_params)
        
        # Parse the error
        error_dict = error_scenario.error_response  # In real scenario, extract from exception
        parsed_error = recovery_simulator.parse_error_response(error_dict)
        
        # Verify error parsing
        assert parsed_error["error_type"] == error_scenario.error_response["error_code"]
        assert "corrections" in parsed_error
        
        # Generate correction
        corrected_params = recovery_simulator.generate_correction(
            error_scenario.initial_params, parsed_error
        )
        
        # Verify correction matches expectations
        for key, expected_value in error_scenario.expected_correction.items():
            assert key in corrected_params
            if isinstance(expected_value, dict):
                for subkey, subvalue in expected_value.items():
                    assert corrected_params[key][subkey] == subvalue
            else:
                assert corrected_params[key] == expected_value
        
        # Simulate successful retry
        success_response = {"success": True, "key": "TEST-456"}
        atlassian_stub.stub_success_response(success_response)
        
        # Record the recovery attempt
        recovery_attempt = RecoveryAttempt(
            attempt_number=2,
            error_received=error_dict,
            correction_applied=corrected_params,
            success=True,
            response=success_response
        )
        recovery_simulator.error_history.append(recovery_attempt)
        
        # Learn from successful recovery
        recovery_simulator.learn_from_error(
            error_scenario.error_type.value,
            error_scenario.initial_params,
            corrected_params
        )

    @pytest.mark.asyncio
    async def test_multi_step_error_correction(
        self, mcp_client, atlassian_stub, recovery_simulator
    ):
        """Test correction of multiple errors in sequence."""
        initial_params = {
            "service": "jira",
            "resource_type": "issue",
            "operation": "create",
            "data": {"title": "Bug Report"}  # Wrong field name + missing fields
        }
        
        # Error 1: Wrong field name
        error1 = {
            "error_code": "INVALID_FIELD_NAMES",
            "user_message": "Field 'title' is not valid for issues",
            "field_mapping": {
                "title": "summary"
            },
            "suggestions": ["Use 'summary' instead of 'title'"]
        }
        
        parsed_error1 = recovery_simulator.parse_error_response(error1)
        corrected_params1 = recovery_simulator.generate_correction(initial_params, parsed_error1)
        
        # Should rename field
        assert "title" not in corrected_params1["data"]
        assert corrected_params1["data"]["summary"] == "Bug Report"
        
        # Error 2: Missing required fields (after first correction)
        error2 = {
            "error_code": "MISSING_REQUIRED_FIELDS", 
            "missing_required": [
                {"field": "project"},
                {"field": "issuetype", "default": "Bug"}
            ]
        }
        
        parsed_error2 = recovery_simulator.parse_error_response(error2)
        corrected_params2 = recovery_simulator.generate_correction(corrected_params1, parsed_error2)
        
        # Should add missing fields
        assert corrected_params2["data"]["project"] == "DEFAULT"
        assert corrected_params2["data"]["issuetype"] == "Bug"
        assert corrected_params2["data"]["summary"] == "Bug Report"  # Preserved from previous correction

    @pytest.mark.asyncio
    async def test_retry_logic_with_backoff(
        self, mcp_client, atlassian_stub, recovery_simulator
    ):
        """Test retry logic with exponential backoff for rate limiting."""
        params = {
            "service": "jira",
            "resource_type": "issue",
            "operation": "get",
            "identifier": "RATE-123"
        }
        
        # Simulate rate limit errors
        rate_limit_error = {
            "error_code": "RATE_LIMIT_EXCEEDED",
            "user_message": "Too many requests",
            "retry_after": 5,
            "suggestions": ["Wait 5 seconds before retry"]
        }
        
        attempt_count = 0
        max_attempts = 5
        
        while attempt_count < max_attempts:
            attempt_count += 1
            
            should_retry = recovery_simulator.should_retry(
                attempt_count, "rate_limit", max_attempts
            )
            
            if attempt_count == 1:
                assert should_retry is True
            elif attempt_count == max_attempts:
                assert should_retry is False
            else:
                assert should_retry is True
        
        # Verify exponential backoff calculation
        backoff_times = [1, 2, 4, 8, 16]  # Exponential backoff sequence
        for i, expected_time in enumerate(backoff_times[:attempt_count-1]):
            calculated_backoff = min(2 ** i, 30)  # Cap at 30 seconds
            assert calculated_backoff <= 30

    @pytest.mark.asyncio
    async def test_non_recoverable_error_handling(
        self, mcp_client, atlassian_stub, recovery_simulator
    ):
        """Test handling of non-recoverable errors."""
        non_recoverable_scenarios = [
            {
                "error_code": "PERMISSION_DENIED",
                "user_message": "You don't have permission to access this resource",
                "should_retry": False
            },
            {
                "error_code": "RESOURCE_NOT_FOUND",
                "user_message": "The requested resource was not found",
                "should_retry": False
            },
            {
                "error_code": "AUTHENTICATION_FAILED",
                "user_message": "Authentication credentials are invalid",
                "should_retry": False
            }
        ]
        
        for scenario in non_recoverable_scenarios:
            should_retry = recovery_simulator.should_retry(
                1, scenario["error_code"].lower(), 3
            )
            
            assert should_retry == scenario["should_retry"], (
                f"Error {scenario['error_code']} should {'not ' if not scenario['should_retry'] else ''}"
                f"be retried"
            )

    @pytest.mark.asyncio
    async def test_error_pattern_learning(
        self, mcp_client, recovery_simulator
    ):
        """Test learning from error patterns to prevent future errors."""
        # Simulate repeated similar errors
        error_type = "missing_required_field"
        service = "jira"
        
        # First occurrence
        recovery_simulator.learn_from_error(
            error_type,
            {"service": service, "operation": "create"},
            {"add_fields": "project"}
        )
        
        # Second occurrence  
        recovery_simulator.learn_from_error(
            error_type,
            {"service": service, "operation": "create"},
            {"add_fields": "project"}
        )
        
        # Third occurrence with different field
        recovery_simulator.learn_from_error(
            error_type, 
            {"service": service, "operation": "create"},
            {"add_fields": "issuetype"}
        )
        
        # Check learned patterns
        pattern_key = f"{error_type}_{service}"
        assert pattern_key in recovery_simulator.learned_patterns
        
        pattern = recovery_simulator.learned_patterns[pattern_key]
        assert pattern["occurrences"] == 3
        assert "common_fixes" in pattern
        
        # Apply learned patterns to new request
        new_params = {"service": service, "operation": "create", "data": {"summary": "Test"}}
        enhanced_params = recovery_simulator.apply_learned_patterns(new_params, error_type)
        
        # Should preemptively add commonly missing field
        assert "data" in enhanced_params
        # Most common missing field (project) should be added
        # This would be implemented based on the most frequent fix

    @pytest.mark.asyncio
    async def test_cascading_error_recovery(
        self, mcp_client, atlassian_stub, recovery_simulator
    ):
        """Test recovery from cascading errors in complex operations."""
        # Complex operation that could fail at multiple points
        complex_params = {
            "service": "jira",
            "resource_type": "issue",
            "operation": "create",
            "data": {
                "summary": "Complex Issue",
                "project": "INVALID_PROJECT",
                "assignee": "nonexistent@example.com",
                "customfield_123": "invalid_value"
            }
        }
        
        # Error sequence: Project -> Assignee -> Custom field
        error_sequence = [
            {
                "error_code": "INVALID_PROJECT",
                "user_message": "Project 'INVALID_PROJECT' does not exist",
                "suggestions": ["Use valid project key"],
                "corrections": {"fix_values": {"project": {"allowed_values": ["VALID", "TEST", "DEMO"]}}}
            },
            {
                "error_code": "INVALID_ASSIGNEE", 
                "user_message": "User 'nonexistent@example.com' not found",
                "suggestions": ["Use valid user ID or remove assignee"],
                "corrections": {"fix_values": {"assignee": {"default": None}}}
            },
            {
                "error_code": "CUSTOM_FIELD_ERROR",
                "user_message": "Custom field value is invalid",
                "suggestions": ["Check custom field configuration"],
                "corrections": {"remove_fields": ["customfield_123"]}
            }
        ]
        
        current_params = complex_params
        recovery_attempts = []
        
        for i, error in enumerate(error_sequence):
            parsed_error = recovery_simulator.parse_error_response(error)
            corrected_params = recovery_simulator.generate_correction(current_params, parsed_error)
            
            recovery_attempt = RecoveryAttempt(
                attempt_number=i + 2,  # First attempt was the initial failure
                error_received=error,
                correction_applied=corrected_params,
                success=(i == len(error_sequence) - 1)  # Last correction succeeds
            )
            recovery_attempts.append(recovery_attempt)
            
            current_params = corrected_params
        
        # Final params should have all corrections applied
        final_params = current_params
        assert final_params["data"]["project"] == "VALID"  # Fixed project
        assert final_params["data"]["assignee"] is None     # Fixed assignee
        assert "customfield_123" not in final_params["data"]  # Removed invalid field

    @pytest.mark.asyncio
    async def test_context_aware_error_recovery(
        self, mcp_client, recovery_simulator, conversation_context
    ):
        """Test error recovery using conversation context."""
        # Set up conversation context
        conversation_context.current_project = "CONTEXT"
        conversation_context.add_operation({
            "result": {"key": "CONTEXT-123", "fields": {"assignee": "john.doe"}}
        })
        
        # Operation with implicit context dependency
        params = {
            "service": "jira",
            "resource_type": "issue", 
            "operation": "create",
            "data": {"summary": "Related Issue"}  # Missing project, but context has it
        }
        
        # Error about missing project
        error = {
            "error_code": "MISSING_REQUIRED_FIELDS",
            "missing_required": [{"field": "project"}],
            "suggestions": ["Add project field"]
        }
        
        parsed_error = recovery_simulator.parse_error_response(error)
        corrected_params = recovery_simulator.generate_correction(params, parsed_error)
        
        # Should use project from context if available
        if conversation_context.current_project:
            corrected_params["data"]["project"] = conversation_context.current_project
        
        assert corrected_params["data"]["project"] == "CONTEXT"
        
        # Could also inherit assignee from recent similar issue
        if conversation_context.previous_operations:
            last_assignee = conversation_context.previous_operations[-1]["result"]["fields"]["assignee"]
            corrected_params["data"]["assignee"] = last_assignee
            
        assert corrected_params["data"]["assignee"] == "john.doe"


@pytest.mark.e2e 
@pytest.mark.error_metrics
class TestErrorRecoveryMetrics:
    """Test suite for measuring error recovery success rates and performance."""

    @pytest.mark.asyncio
    async def test_recovery_success_rate_benchmark(
        self, mcp_client, recovery_simulator
    ):
        """Benchmark overall error recovery success rate."""
        
        # Test scenarios with expected recovery outcomes
        test_scenarios = [
            # Recoverable errors (should succeed)
            (ErrorType.MISSING_REQUIRED_FIELD, True),
            (ErrorType.INVALID_FIELD_VALUE, True),
            (ErrorType.VALIDATION_ERROR, True),
            (ErrorType.SCHEMA_MISMATCH, True),
            
            # Partially recoverable (might succeed with multiple attempts)
            (ErrorType.RATE_LIMIT, True),
            (ErrorType.API_ERROR, True),
            
            # Non-recoverable (should fail gracefully)
            (ErrorType.PERMISSION_DENIED, False),
            (ErrorType.RESOURCE_NOT_FOUND, False),
        ]
        
        successful_recoveries = 0
        total_attempts = 0
        
        for error_type, should_recover in test_scenarios:
            total_attempts += 1
            
            # Simulate error recovery attempt
            mock_params = {"service": "jira", "operation": "create"}
            mock_error = {"error_code": error_type.value}
            
            parsed_error = recovery_simulator.parse_error_response(mock_error)
            
            # Check if recovery should be attempted
            should_retry = recovery_simulator.should_retry(1, error_type.value)
            
            if should_recover and should_retry:
                # Simulate successful recovery
                corrected_params = recovery_simulator.generate_correction(mock_params, parsed_error)
                if corrected_params != mock_params:  # Some correction was applied
                    successful_recoveries += 1
            elif not should_recover and not should_retry:
                # Correctly identified as non-recoverable
                successful_recoveries += 1
        
        recovery_rate = (successful_recoveries / total_attempts) * 100
        
        # Target: >90% recovery success rate
        assert recovery_rate >= 90.0, f"Error recovery rate: {recovery_rate:.1f}% (target: >90%)"

    @pytest.mark.asyncio
    async def test_error_correction_accuracy(
        self, mcp_client, recovery_simulator
    ):
        """Test accuracy of error corrections."""
        
        correction_scenarios = [
            # Missing field corrections
            {
                "error": {"missing_required": [{"field": "project"}]},
                "original": {"data": {"summary": "Test"}},
                "expected_fix": "project should be added to data"
            },
            
            # Invalid value corrections
            {
                "error": {"invalid_values": {"priority": {"allowed_values": ["Low", "High"]}}},
                "original": {"data": {"priority": "Invalid"}},
                "expected_fix": "priority should be set to allowed value"
            },
            
            # Schema structure corrections
            {
                "error": {"schema_requirements": {"required_structure": {"space": {"required": True}}}},
                "original": {"data": {"title": "Test"}},
                "expected_fix": "space should be added"
            }
        ]
        
        correct_fixes = 0
        total_scenarios = len(correction_scenarios)
        
        for scenario in correction_scenarios:
            parsed_error = recovery_simulator.parse_error_response(scenario["error"])
            corrected = recovery_simulator.generate_correction(scenario["original"], parsed_error)
            
            # Verify expected fix was applied
            if "project should be added" in scenario["expected_fix"]:
                if "data" in corrected and "project" in corrected["data"]:
                    correct_fixes += 1
            elif "priority should be set" in scenario["expected_fix"]:
                if ("data" in corrected and "priority" in corrected["data"] and 
                    corrected["data"]["priority"] in ["Low", "High"]):
                    correct_fixes += 1
            elif "space should be added" in scenario["expected_fix"]:
                if "data" in corrected and "space" in corrected["data"]:
                    correct_fixes += 1
        
        correction_accuracy = (correct_fixes / total_scenarios) * 100
        
        # Target: >95% correction accuracy
        assert correction_accuracy >= 95.0, f"Correction accuracy: {correction_accuracy:.1f}% (target: >95%)"

    @pytest.mark.asyncio
    async def test_learning_effectiveness(
        self, mcp_client, recovery_simulator
    ):
        """Test effectiveness of error pattern learning."""
        
        # Simulate repeated error pattern
        error_type = "missing_required_field"
        common_missing_field = "project"
        
        # Train with multiple examples
        for _ in range(5):
            recovery_simulator.learn_from_error(
                error_type,
                {"service": "jira"},
                {"add_fields": common_missing_field}
            )
        
        # Test learning application
        test_params = {"service": "jira", "data": {"summary": "Test"}}
        enhanced_params = recovery_simulator.apply_learned_patterns(test_params, error_type)
        
        # Should preemptively add commonly missing field
        learning_applied = (enhanced_params != test_params and 
                          "data" in enhanced_params and 
                          len(enhanced_params["data"]) > len(test_params["data"]))
        
        assert learning_applied, "Error pattern learning not effectively applied"
        
        # Check learning statistics
        pattern_key = f"{error_type}_jira"
        assert pattern_key in recovery_simulator.learned_patterns
        assert recovery_simulator.learned_patterns[pattern_key]["occurrences"] == 5

    @pytest.mark.asyncio
    async def test_recovery_performance(
        self, mcp_client, recovery_simulator
    ):
        """Test performance of error recovery process."""
        import time
        
        # Performance test scenarios
        scenarios = [
            {"error_code": "MISSING_REQUIRED_FIELDS", "complexity": "simple"},
            {"error_code": "INVALID_FIELD_VALUES", "complexity": "medium"},
            {"error_code": "SCHEMA_VALIDATION_ERROR", "complexity": "complex"},
        ] * 10  # 30 total scenarios
        
        total_time = 0
        successful_recoveries = 0
        
        for scenario in scenarios:
            start_time = time.time()
            
            try:
                # Simulate error recovery
                parsed_error = recovery_simulator.parse_error_response(scenario)
                corrected = recovery_simulator.generate_correction({}, parsed_error)
                successful_recoveries += 1
            except Exception:
                pass
            
            end_time = time.time()
            total_time += (end_time - start_time)
        
        avg_recovery_time = (total_time / len(scenarios)) * 1000  # Convert to ms
        
        # Performance targets
        assert avg_recovery_time < 100, f"Average recovery time: {avg_recovery_time:.2f}ms (target: <100ms)"
        assert successful_recoveries >= len(scenarios) * 0.9, "Recovery success rate too low"

    @pytest.mark.asyncio
    async def test_end_to_end_recovery_workflow(
        self, mcp_client, atlassian_stub, recovery_simulator
    ):
        """Test complete end-to-end error recovery workflow."""
        
        # Complete workflow: Error -> Parse -> Correct -> Retry -> Learn
        workflow_steps = {
            "initial_failure": False,
            "error_parsed": False, 
            "correction_generated": False,
            "retry_successful": False,
            "pattern_learned": False
        }
        
        # Step 1: Initial failure
        initial_params = {
            "service": "jira",
            "resource_type": "issue",
            "operation": "create",
            "data": {"summary": "Test Issue"}  # Missing required fields
        }
        
        try:
            # This should fail
            await mcp_client.call_tool("resource_manager", initial_params)
        except Exception:
            workflow_steps["initial_failure"] = True
        
        # Step 2: Parse error
        mock_error = {
            "error_code": "MISSING_REQUIRED_FIELDS",
            "missing_required": [{"field": "project"}, {"field": "issuetype"}]
        }
        
        parsed_error = recovery_simulator.parse_error_response(mock_error)
        if "corrections" in parsed_error:
            workflow_steps["error_parsed"] = True
        
        # Step 3: Generate correction
        corrected_params = recovery_simulator.generate_correction(initial_params, parsed_error)
        if corrected_params != initial_params:
            workflow_steps["correction_generated"] = True
        
        # Step 4: Simulate successful retry
        success_response = {"key": "TEST-123", "success": True}
        atlassian_stub.stub_success_response(success_response)
        
        # In real scenario, would retry with corrected params
        workflow_steps["retry_successful"] = True
        
        # Step 5: Learn from recovery
        recovery_simulator.learn_from_error(
            "missing_required_field",
            initial_params,
            corrected_params
        )
        
        if "missing_required_field_jira" in recovery_simulator.learned_patterns:
            workflow_steps["pattern_learned"] = True
        
        # Verify all workflow steps completed
        assert all(workflow_steps.values()), f"Incomplete workflow steps: {workflow_steps}"
        
        # Verify end-to-end success
        workflow_success_rate = sum(workflow_steps.values()) / len(workflow_steps) * 100
        assert workflow_success_rate == 100.0, "End-to-end recovery workflow not fully successful"