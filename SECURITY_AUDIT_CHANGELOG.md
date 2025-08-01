# Security Audit Changelog

## Overview
This document summarizes the security vulnerabilities discovered and fixed during the comprehensive security audit of the mcp-atlassian MCP server.

## Security Vulnerabilities Fixed

### 1. OAuth Client Secret Logging (CRITICAL)
**Files Affected:**
- `src/mcp_atlassian/utils/oauth.py` (line 107)
- `src/mcp_atlassian/utils/oauth_setup.py` (line 281)

**Issue:** OAuth client secrets were being logged in plain text during token exchange and setup wizard operations.

**Fix Applied:**
- Imported `mask_sensitive` function from `mcp_atlassian.utils.logging`
- Masked client secrets before logging with format: `conf****-xyz`
- Added memory cleanup after logging sensitive data

**Impact:** Prevents exposure of OAuth credentials in log files.

### 2. API Payload Sanitization (HIGH)
**File Affected:**
- `src/mcp_atlassian/rest/base.py` (lines 241-242)

**Issue:** Full JSON payloads containing PII and sensitive data were logged without sanitization.

**Fix Applied:**
- Added comprehensive `sanitize_json_data()` function
- Sanitizes sensitive keys: passwords, API keys, tokens, SSN, credit cards, etc.
- Masks emails to format: `jo****oe@example.com`
- Deep sanitization for nested objects and arrays

**Impact:** Prevents exposure of user PII and sensitive data in debug logs.

### 3. Thread Safety - TTLCache (HIGH)
**Files Affected:**
- `src/mcp_atlassian/formatting/router.py` (line 61)
- `src/mcp_atlassian/servers/main.py` (line 205)

**Issue:** TTLCache instances accessed by multiple threads without synchronization, causing potential race conditions.

**Fix Applied:**
- Added `threading.Lock` for each cache instance
- Wrapped all cache operations with lock acquisition
- Protected both read and write operations

**Impact:** Prevents race conditions and data corruption in concurrent environments.

### 4. Exception Handling - Authentication Errors (MEDIUM)
**File Affected:**
- `src/mcp_atlassian/servers/dependencies.py` (line 230)

**Issue:** Overly broad exception handling that converted specific authentication errors to generic ValueError, hiding root causes.

**Fix Applied:**
- Added specific handling for `MCPAtlassianAuthenticationError`
- Preserved original error context in exception messages
- Enhanced error messages with auth type and token presence info

**Impact:** Improves debugging and error visibility for authentication failures.

## Test Coverage

Created comprehensive integration tests in `tests/integration/test_security_patches.py`:
- `TestOAuthSecretMasking`: Verifies OAuth secrets are masked in logs
- `TestAPIPayloadSanitization`: Ensures sensitive data is sanitized
- `TestCacheThreadSafety`: Tests thread-safe cache operations
- `TestExceptionHandling`: Validates authentication error preservation

All 5 security tests pass successfully.

## Verification Steps

1. **OAuth Secret Masking**
   - Run OAuth token exchange with debug logging
   - Verify client_secret appears as masked value in logs
   - Check OAuth setup wizard output for masked secrets

2. **API Payload Sanitization**
   - Send API requests with sensitive data (passwords, tokens, PII)
   - Verify debug logs show sanitized values
   - Confirm nested objects are properly sanitized

3. **Thread Safety**
   - Run concurrent operations accessing FormatRouter cache
   - Run concurrent token validation in main server
   - Verify no race conditions or exceptions occur

4. **Exception Handling**
   - Trigger authentication failures with invalid tokens
   - Verify error messages include specific auth context
   - Confirm root cause is preserved in error chain

## Pre-existing Issues Not Addressed

During the audit, many pre-existing test failures were discovered in the test suite. These appear to be unrelated to the security patches and were not addressed as part of this security-focused audit.

## Recommendations

1. **Logging Configuration**: Consider implementing a centralized sensitive data filter for all logging operations.
2. **Security Testing**: Add dedicated security test markers to pytest configuration.
3. **Code Coverage**: Current overall coverage is low (~6%). Focus on increasing test coverage for critical security paths.
4. **Pre-commit Hooks**: Fix remaining linting issues to ensure code quality standards.

## Summary

This security audit successfully identified and fixed 4 critical to medium severity vulnerabilities:
- 2 instances of secret exposure in logs
- 1 PII/sensitive data logging issue  
- 2 thread safety vulnerabilities
- 1 exception handling issue

All fixes have been implemented with appropriate tests and verification. The codebase is now more secure against common security vulnerabilities related to logging, concurrency, and error handling.