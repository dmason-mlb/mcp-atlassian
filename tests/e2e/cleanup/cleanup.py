import asyncio
import json
import os
from pathlib import Path
from typing import Any

from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession


ROOT_DIR = Path(__file__).resolve().parents[3]

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
                # Drop inline comments or command separators
                if ' #' in val:
                    val = val.split(' #', 1)[0]
                if ' ;' in val:
                    val = val.split(' ;', 1)[0]
                val = val.strip().strip('"').strip("'")
                os.environ.setdefault(key, val)
    except Exception:
        pass

_load_env_file(ROOT_DIR / ".env")

ART_DIR = ROOT_DIR / "e2e" / ".artifacts"
SEED_PATH = ART_DIR / "seed.json"


def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def extract_json(result: Any) -> dict:
    try:
        content = getattr(result, "content", None) or result.get("content")
        if isinstance(content, list) and content:
            for item in content:
                text = item.get("text") if isinstance(item, dict) else getattr(item, "text", None)
                if text:
                    try:
                        return json.loads(text)
                    except Exception:
                        continue
    except Exception:
        pass
    try:
        return json.loads(str(result))
    except Exception:
        return {}


async def main() -> None:
    mcp_url = os.getenv("MCP_URL", "http://localhost:9000/mcp")

    jira_project = required("JIRA_PROJECT")
    confluence_space = required("CONFLUENCE_SPACE")

    seed = json.loads(SEED_PATH.read_text()) if SEED_PATH.exists() else {}
    label = seed.get("label") or os.getenv("SEED_LABEL")
    if not label:
        raise RuntimeError("No SEED label found to clean up")

    headers: dict[str, str] = {}
    if os.getenv("USER_OAUTH_TOKEN"):
        headers["Authorization"] = f"Bearer {os.getenv('USER_OAUTH_TOKEN')}"
    if os.getenv("USER_CLOUD_ID"):
        headers["X-Atlassian-Cloud-Id"] = os.getenv("USER_CLOUD_ID", "")

    async with streamablehttp_client(mcp_url, headers=headers) as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()

            # Jira: find and delete by label
            jql = f"project = {jira_project} AND labels = {label}"
            search_res = await session.call_tool(
                "jira_search", {"jql": jql, "limit": 50}
            )
            search_obj = extract_json(search_res)
            for issue in search_obj.get("issues", []):
                key = issue.get("key")
                if key:
                    await session.call_tool("jira_delete_issue", {"issue_key": key})

            # Confluence: search by CQL label and space
            cql = f"label = '{label}' AND space = {confluence_space}"
            conf_res = await session.call_tool(
                "confluence_search", {"query": cql, "limit": 50}
            )
            conf_obj = extract_json(conf_res)
            for page in conf_obj.get("results", []):
                page_id = page.get("id") or page.get("page_id")
                if page_id:
                    await session.call_tool("confluence_delete_page", {"page_id": str(page_id)})

            print("Cleanup complete")


if __name__ == "__main__":
    asyncio.run(main())
