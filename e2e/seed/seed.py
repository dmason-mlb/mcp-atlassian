import asyncio
import json
import os
from pathlib import Path
from typing import Any

from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession


ROOT_DIR = Path(__file__).resolve().parents[2]

# .env loader (use python-dotenv if available, else minimal parser)
def _load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return
    try:
        try:
            from dotenv import load_dotenv as _dz

            _dz(env_path, override=False)
            return
        except Exception:
            pass
        for raw in env_path.read_text().splitlines():
            line = raw.strip()
            if not line or line.strip().startswith('#'):
                continue
            if line.startswith('export '):
                line = line[len('export '):].lstrip()
            if '=' in line:
                key, val = line.split('=', 1)
                key = key.strip()
                # Drop inline comments
                if ' #' in val:
                    val = val.split(' #', 1)[0]
                if ' ;' in val:
                    val = val.split(' ;', 1)[0]
                val = val.strip().strip('"').strip("'")
                os.environ.setdefault(key, val)
    except Exception:
        pass

# Load project root .env so running from e2e/ works
_load_env_file(ROOT_DIR / ".env")

ART_DIR = ROOT_DIR / "e2e" / ".artifacts"
ART_DIR.mkdir(parents=True, exist_ok=True)
SEED_PATH = ART_DIR / "seed.json"


def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def md_fixture() -> str:
    return (
        "# Formatting Elements Being Tested\n\n"
        "## Test Objectives\n\n"
        "- Bullet Points\n"
        "- Numbered Lists\n\n"
        "1. One\n2. Two\n\n"
        "> Blockquote\n\n"
        "`inline code`\n\n"
        "```\n"
        "ts code block\n"
        "console.log('hello');\n"
        "```\n\n"
        "| Col A | Col B |\n"
        "| --- | --- |\n"
        "| A | B |\n\n"
        "Panel: IMPORTANT\n"
    )


def extract_json(result: Any) -> dict:
    """Best-effort extract JSON object from MCP tool result."""
    if isinstance(result, dict):
        return result
    try:
        # FastMCP ToolResult shape
        content = getattr(result, "content", None) or result.get("content")
        if isinstance(content, list) and content:
            # Prefer text blocks that contain JSON
            for item in content:
                text = item.get("text") if isinstance(item, dict) else getattr(item, "text", None)
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


async def main() -> None:
    mcp_url = os.getenv("MCP_URL", "http://localhost:9000/mcp")
    label = os.getenv("SEED_LABEL", f"mcp-e2e-{os.getpid()}")

    # Atlassian env
    jira_project = required("JIRA_PROJECT")
    # Derive base URLs. Prefer explicit JIRA_BASE/CONFLUENCE_BASE, else fall back to ATLASSIAN_URL
    jira_base = os.getenv("JIRA_BASE") or required("ATLASSIAN_URL")
    confluence_space = required("CONFLUENCE_SPACE")
    confluence_base = os.getenv("CONFLUENCE_BASE") or f"{jira_base.rstrip('/')}/wiki"

    # Optional auth passthrough for multi-tenant server
    headers: dict[str, str] = {}
    if os.getenv("USER_OAUTH_TOKEN"):
        headers["Authorization"] = f"Bearer {os.getenv('USER_OAUTH_TOKEN')}"
    if os.getenv("USER_CLOUD_ID"):
        headers["X-Atlassian-Cloud-Id"] = os.getenv("USER_CLOUD_ID", "")

    async with streamablehttp_client(mcp_url, headers=headers) as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()

            # Create Jira issue
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
            print(f"Extracted JSON: {jira_obj}")
            issue_key = jira_obj.get("key") or jira_obj.get("issue_key")

            # Add comment
            if issue_key:
                await session.call_tool(
                    "jira_issues_add_comment",
                    {
                        "issue_key": issue_key,
                        "comment": "E2E seed comment with `code` and bold **text**.",
                    },
                )

            # Prepare and upload attachments (optional): text + image copy if available
            if issue_key:
                try:
                    # Create a small text artifact
                    text_path = ART_DIR / "test-attachment.txt"
                    text_path.write_text("This is an E2E attachment file. Label: " + label)
                    await session.call_tool(
                        "jira_management_upload_attachment",
                        {"issue_key": issue_key, "file_path": str(text_path)},
                    )
                except Exception:
                    pass

                # Copy provided image if it exists on this machine
                img_src = Path("/Users/douglas.mason/Downloads/android-japanese-watch-tab.png")
                if img_src.exists():
                    try:
                        img_dst = ART_DIR / "test-image.png"
                        img_dst.write_bytes(img_src.read_bytes())
                        await session.call_tool(
                            "jira_management_upload_attachment",
                            {"issue_key": issue_key, "file_path": str(img_dst)},
                        )
                    except Exception:
                        pass

            # Create Confluence page
            print(f"Creating Confluence page in space {confluence_space} with label {label}")
            conf_create = await session.call_tool(
                "confluence_pages_create_page",
                {
                    "space_key": confluence_space,
                    "title": f"[E2E] Visual Render Validation {label}",
                    "content": md_fixture(),
                    "content_format": "markdown",
                },
            )
            print(f"Confluence create response: {conf_create}")
            conf_obj = extract_json(conf_create)
            print(f"Extracted Confluence JSON: {conf_obj}")
            page_id = conf_obj.get("id") or conf_obj.get("page_id") or conf_obj.get("data", {}).get("id")

            # Add label for cleanup/querying
            if page_id:
                try:
                    await session.call_tool(
                        "confluence_content_add_label",
                        {"page_id": str(page_id), "name": label},
                    )
                except Exception:
                    pass

            result = {
                "label": label,
                "jira": {
                    "issueKey": issue_key,
                    "issueUrl": f"{jira_base}/browse/{issue_key}" if issue_key else None,
                },
                "confluence": {
                    "pageId": page_id,
                    # Let Confluence redirect to full title path
                    "pageUrl": f"{confluence_base}/spaces/{confluence_space}/pages/{page_id}" if page_id else None,
                },
            }

            SEED_PATH.write_text(json.dumps(result, indent=2))
            print(f"Seed complete: {SEED_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
