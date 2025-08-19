#!/usr/bin/env python3

import asyncio
import json
import os
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


def md_fixture() -> str:
    return """# Test Objectives

This is E2E test content for visual render validation.

## Bullet Points
- First bullet point
- Second bullet point
- Third bullet point

## Numbered Lists
1. One
2. Two
3. Three

## Code Examples
Here is some `inline code` for testing.

```javascript
console.log("Hello, world!");
```

## Tables
| Col A | Col B |
|-------|-------|
| A     | B     |
| 1     | 2     |

## Blockquote
> This is a Blockquote for testing purposes.

**Bold text** and *italic text* for formatting validation."""


def extract_json(result):
    """Best-effort extract JSON object from MCP tool result."""
    if isinstance(result, dict):
        return result
    try:
        # FastMCP ToolResult shape
        content = getattr(result, "content", None) or result.get("content")
        if isinstance(content, list) and content:
            # Prefer text blocks that contain JSON
            for item in content:
                text = (
                    item.get("text")
                    if isinstance(item, dict)
                    else getattr(item, "text", None)
                )
                if text:
                    try:
                        return json.loads(text)
                    except Exception:
                        continue
    except Exception:
        pass
    # Fallback: try json.loads on str(result)
    try:
        return json.loads(str(result))
    except Exception:
        return {}


async def create_seed_data():
    """Create seed data similar to what the seed script does."""
    mcp_url = "http://localhost:9000/mcp"
    label = f"mcp-e2e-{os.getpid()}"

    # Use environment variables
    jira_project = os.getenv("JIRA_PROJECT", "FTEST")
    confluence_space = os.getenv("CONFLUENCE_SPACE", "655361")
    atlassian_url = os.getenv("ATLASSIAN_URL", "https://baseball.atlassian.net")

    async with streamablehttp_client(mcp_url) as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()

            print(f"Creating Jira issue in project {jira_project} with label {label}")
            jira_create = await session.call_tool(
                "jira_issues_create_issue",
                {
                    "project_key": jira_project,
                    "summary": f"[E2E] Visual Render Validation {label}",
                    "issue_type": "Task",
                    "description": md_fixture(),
                    "additional_fields": {"labels": [label]},
                },
            )
            print(f"Jira create response: {jira_create}")
            jira_obj = extract_json(jira_create)
            issue_key = (
                jira_obj.get("key")
                or jira_obj.get("issue_key")
                or jira_obj.get("issue", {}).get("key")
            )

            # Create Confluence page
            print(
                f"Creating Confluence page in space {confluence_space} with label {label}"
            )
            conf_create = await session.call_tool(
                "confluence_pages_create_page",
                {
                    "space_id": confluence_space,
                    "title": f"[E2E] Visual Render Validation {label}",
                    "content": md_fixture(),
                    "content_format": "markdown",
                },
            )
            print(f"Confluence create response: {conf_create}")
            conf_obj = extract_json(conf_create)
            page_id = (
                conf_obj.get("page", {}).get("id")
                or conf_obj.get("id")
                or conf_obj.get("page_id")
                or conf_obj.get("data", {}).get("id")
            )

            # Create seed.json
            result = {
                "label": label,
                "jira": {
                    "issueKey": issue_key,
                    "issueUrl": f"{atlassian_url}/browse/{issue_key}"
                    if issue_key
                    else None,
                },
                "confluence": {
                    "pageId": page_id,
                    "pageUrl": f"{atlassian_url}/wiki/spaces/{confluence_space}/pages/{page_id}"
                    if page_id
                    else None,
                },
            }

            # Write to both locations
            root_dir = Path(__file__).resolve().parent
            art_dir = root_dir / "e2e" / ".artifacts"
            art_dir.mkdir(parents=True, exist_ok=True)
            seed_path = art_dir / "seed.json"

            # Also write to tests/e2e/.artifacts for current directory
            test_art_dir = root_dir / "tests" / "e2e" / ".artifacts"
            test_art_dir.mkdir(parents=True, exist_ok=True)
            test_seed_path = test_art_dir / "seed.json"

            seed_content = json.dumps(result, indent=2)
            seed_path.write_text(seed_content)
            test_seed_path.write_text(seed_content)

            print(f"Seed complete: {seed_path}")
            print(f"Also written to: {test_seed_path}")
            print(f"Result: {result}")

            return result


if __name__ == "__main__":
    asyncio.run(create_seed_data())
