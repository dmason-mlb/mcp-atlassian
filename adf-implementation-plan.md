# MCP Atlassian ADF Implementation Plan

**Created:** July 29, 2025
**Purpose:** Convert Claude Code-generated markdown to proper ADF format for Jira/Confluence Cloud
**Problem:** Asterisks and underscores appearing literally instead of formatted text

## Executive Summary

This plan implements a hybrid markdown formatting system that automatically detects Atlassian deployment types and uses appropriate formatting:
- **Cloud instances**: Convert markdown to ADF (Atlassian Document Format) JSON
- **Server/DC instances**: Continue using wiki markup strings
- **Backward compatibility**: Maintain existing functionality while adding new capabilities

## Architecture Overview

```
Markdown Input
     |
     v
Format Router -----> Deployment Detection
     |                      |
     v                      v
[Cloud Detected]      [Server/DC Detected]
     |                      |
     v                      v
ADF Generator         Wiki Markup Converter
     |                      |
     v                      v
ADF JSON Output       Wiki String Output
     |                      |
     v                      v
Jira/Confluence Cloud API   Server/DC API
```

## Implementation Phases

### Phase 1: Foundation & Research (Steps 1-3)

#### Step 1: Project Initialization and Scope Definition
- **Objective**: Establish project foundation and validate approach
- **Activities**:
  - Analyze current formatting issues in detail
  - Research ADF specification and existing conversion libraries
  - Define success criteria and validation methods
  - Create project structure and documentation framework

#### Step 2: Research and Requirements Analysis
- **Objective**: Gather technical requirements and validate assumptions
- **Key Research Areas**:
  - ADF format specification deep dive and schema validation requirements
  - Current preprocessing pipeline architecture analysis (JiraPreprocessor, ConfluencePreprocessor)
  - Deployment detection mechanisms (Cloud vs Server/DC)
  - Performance benchmarking requirements for conversion processes
  - Integration points with existing Jira/Confluence operation methods

#### Step 3: Architecture Design and Pipeline Analysis
- **Objective**: Design technical architecture for hybrid formatting system
- **Architecture Components**:
  1. **Format Detection Module**: Determine if instance is Cloud (needs ADF) or Server/DC (needs wiki markup)
  2. **ADF Generator Core**: Python-native markdown-to-ADF converter with extensible element support
  3. **Legacy Wiki Converter**: Enhanced existing wiki markup generator
  4. **Format Router**: Decision logic to select appropriate converter based on deployment type
  5. **Validation Layer**: ADF schema validation and fallback mechanisms

- **Integration Points**:
  - Update JiraPreprocessor.markdown_to_jira() to use format router
  - Modify ConfluencePreprocessor for similar hybrid approach
  - Integrate deployment detection in client configuration
  - Add performance monitoring hooks

- **Key Design Decisions**:
  - Use factory pattern for converter selection
  - Implement progressive ADF element support (start with basic, expand to complex)
  - Create comprehensive error handling with graceful fallbacks
  - Design for easy testing with both deployment types

### Phase 2: Core Implementation (Steps 4-5)

#### Step 4: Core ADF Generator Implementation
- **Objective**: Build Python-native ADF generator with incremental complexity
- **ADF Generator Development Plan**:

1. **Basic Element Support**: Start with fundamental markdown elements:
   - Text with marks (bold, italic, code, strikethrough)
   - Paragraphs and line breaks
   - Headings (H1-H6)
   - Links (inline and reference-style)

2. **Progressive Enhancement**: Add complex elements in phases:
   - Lists (ordered, unordered, nested)
   - Code blocks with language detection
   - Tables (basic structure first)
   - Block quotes and horizontal rules

3. **Implementation Structure**:
   - Create ADFGenerator class in new src/mcp_atlassian/formatting/adf.py
   - Use markdown parser (likely markdown library) to create AST
   - Transform AST nodes to ADF JSON structure with visitor pattern
   - Implement ADF schema validation using JSON schema

4. **Error Handling Strategy**:
   - Graceful degradation for unsupported elements (fallback to plain text)
   - Validation errors trigger fallback to wiki markup
   - Comprehensive logging for debugging format issues

#### Step 5: Integration with Preprocessing Pipeline
- **Objective**: Connect ADF generator with existing infrastructure
- **Pipeline Modification Strategy**:

1. **Create Format Router Module** (src/mcp_atlassian/formatting/router.py):
   - Deployment detection logic (analyze URL patterns, API responses)
   - Format selection based on instance type (Cloud→ADF, Server/DC→wiki)
   - Configuration caching to avoid repeated detection calls

2. **Update Preprocessing Classes**:
   - Modify JiraPreprocessor.markdown_to_jira() to use format router
   - Update ConfluencePreprocessor for similar integration
   - Add format-specific preprocessing hints and metadata

3. **Client Configuration Enhancement**:
   - Add deployment type detection to JiraConfig and ConfluenceConfig
   - Cache detected format to avoid API overhead
   - Provide manual override option for edge cases

4. **Backward Compatibility**:
   - Maintain existing wiki markup converter as fallback
   - Feature flag for ADF enablement during rollout
   - Comprehensive migration testing framework

### Phase 3: Testing & Validation (Steps 6-7)

#### Step 6: Testing Strategy and Validation Framework
- **Objective**: Ensure reliability and compatibility across deployment types
- **Multi-Level Testing Strategy**:

1. **Unit Testing**:
   - ADF generator tests with markdown-to-JSON validation
   - Format router tests with mock deployment configurations
   - Individual element conversion accuracy tests
   - Schema validation and error handling tests

2. **Integration Testing**:
   - Full preprocessing pipeline tests with both formats
   - API compatibility tests against real Jira/Confluence instances
   - Performance benchmarking (target: <100ms conversion time)
   - Cross-deployment testing (Cloud vs Server/DC)

3. **Regression Testing**:
   - Existing functionality validation to ensure no breakage
   - Wiki markup format verification for Server/DC instances
   - Edge case handling (malformed markdown, complex nested structures)

4. **User Acceptance Testing**:
   - Real-world markdown samples from Claude Code usage
   - Visual verification in Jira/Confluence interfaces
   - Format fidelity comparison (markdown → ADF → rendered output)

#### Step 7: Performance Optimization and Error Handling
- **Objective**: Optimize performance and implement robust error handling
- **Performance Optimization Strategy**:

1. **Conversion Efficiency**:
   - Implement caching for frequently converted markdown patterns
   - Optimize AST traversal with efficient data structures
   - Lazy evaluation for complex elements (tables, nested lists)
   - Memory-efficient JSON generation to minimize overhead

2. **Detection Optimization**:
   - Cache deployment type detection results per client instance
   - Implement smart caching with TTL for configuration changes
   - Minimize API calls for deployment type validation

3. **Error Handling Framework**:
   - Graceful degradation hierarchy: ADF → wiki markup → plain text
   - Comprehensive error logging with format context
   - Fallback mechanism activation for conversion failures
   - User feedback for unsupported markdown elements

4. **Monitoring and Diagnostics**:
   - Performance metrics collection (conversion time, success rate)
   - Format selection logging for debugging
   - Error pattern analysis for continuous improvement

### Phase 4: Documentation & Deployment (Step 8)

#### Step 8: Documentation, Deployment, and Memory Management
- **Objective**: Complete implementation with comprehensive documentation
- **Documentation Strategy**:

1. **Technical Documentation**:
   - Update CLAUDE.md with ADF conversion guidance
   - Create ADF generator API documentation with examples
   - Document deployment detection mechanisms and override options
   - Add troubleshooting guide for format conversion issues

2. **User Guidance**:
   - Update formatting issues guide with new ADF solution
   - Create migration guide for existing Server/DC users
   - Provide markdown best practices for optimal ADF conversion

3. **Memory Management and Progress Tracking**:
   - Create repo memory entries for ADF implementation guidance
   - Document progress tracking system for task completion updates
   - Establish maintenance procedures for ADF schema updates

4. **Deployment and Rollback**:
   - Feature flag configuration for gradual ADF rollout
   - Rollback procedures if critical issues arise
   - Monitoring dashboards for deployment health validation

**Final Deliverables**:
- Complete ADF conversion system with backward compatibility
- Comprehensive test suite and performance benchmarks
- Updated documentation and user guidance
- Progress tracking system for ongoing maintenance

## File Structure

```
src/mcp_atlassian/
├── formatting/
│   ├── __init__.py
│   ├── adf.py              # ADF generator implementation
│   ├── router.py           # Format routing and deployment detection
│   └── schemas/
│       └── adf_schema.json # ADF validation schema
├── preprocessing/
│   ├── base.py             # Updated base preprocessing
│   ├── jira.py             # Updated Jira preprocessing
│   └── confluence.py       # Updated Confluence preprocessing
└── config/
    ├── jira.py             # Enhanced with deployment detection
    └── confluence.py       # Enhanced with deployment detection

tests/
├── unit/
│   └── formatting/
│       ├── test_adf.py
│       └── test_router.py
└── integration/
    └── test_adf_integration.py
```

## Success Criteria

1. **Functional Requirements**:
   - Markdown bold/italic renders correctly in Jira/Confluence Cloud
   - Server/DC deployments continue working unchanged
   - Support for common markdown elements (headings, lists, links, code)

2. **Performance Requirements**:
   - ADF conversion completes in <100ms for typical content
   - No significant impact on existing operation response times
   - Deployment detection cached to minimize API overhead

3. **Reliability Requirements**:
   - Graceful fallback to wiki markup if ADF generation fails
   - Comprehensive error logging for troubleshooting
   - 99%+ format conversion success rate

4. **Compatibility Requirements**:
   - Zero breaking changes to existing Server/DC functionality
   - Feature flag support for gradual Cloud rollout
   - Easy rollback mechanism if issues arise

## Risk Mitigation

| Risk | Impact | Mitigation Strategy |
|------|--------|-------------------|
| ADF complexity exceeds expectations | High | Start with basic elements, expand incrementally |
| API compatibility issues | High | Comprehensive testing with real instances |
| Performance degradation | Medium | Benchmarking and optimization throughout development |
| Breaking existing functionality | High | Feature flags and extensive regression testing |
| Deployment detection failures | Medium | Manual override options and comprehensive logging |

## Next Steps

1. **Immediate**: Begin Step 1 research and project setup
2. **Week 1**: Complete ADF specification analysis and prototype basic converter
3. **Week 2**: Implement deployment detection and format routing
4. **Week 3**: Integration testing and performance optimization
5. **Week 4**: Documentation and deployment preparation

---

*This plan provides a comprehensive roadmap for implementing ADF support while maintaining backward compatibility and ensuring reliable operation across all Atlassian deployment types.*
