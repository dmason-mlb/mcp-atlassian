# optimization/context.md

## Project Goal
Refactor MCP Atlassian server from 42 tools to 6-10 meta-tools, reducing token usage by 75%.

## Project Structure
- Base: /Users/douglas.mason/Documents/GitHub/mcp-atlassian.worktrees/develop/
- Source: src/mcp_atlassian/
- Jira tools: src/mcp_atlassian/jira/
- Confluence tools: src/mcp_atlassian/confluence/
- MCP Servers: src/mcp_atlassian/servers/
- Tests: tests/ (unit/, integration/, e2e/)

## Key Files
- Main server: src/mcp_atlassian/servers/
- Jira operations: src/mcp_atlassian/jira/operations.py (likely)
- Confluence operations: src/mcp_atlassian/confluence/operations.py (likely)
- Current token count: ~15,000

## Success Metrics
- [ ] Token usage < 3,500
- [ ] All tests in tests/ pass
- [ ] Meta-tools in src/mcp_atlassian/meta_tools/
- [ ] Version switching in servers/