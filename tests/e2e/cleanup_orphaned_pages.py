#!/usr/bin/env python3
"""
One-time cleanup script for orphaned E2E test pages.

This script searches for and removes Confluence pages with "20250820" in their title
that were created by E2E tests but not properly cleaned up.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any, List, Dict

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

ROOT_DIR = Path(__file__).resolve().parents[3]


def _load_env_file(env_path: Path) -> None:
    """Load environment variables from .env file."""
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
            if not line or line.strip().startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):].lstrip()
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                if " #" in val:
                    val = val.split(" #", 1)[0]
                if " ;" in val:
                    val = val.split(" ;", 1)[0]
                val = val.strip().strip('"').strip("'")
                os.environ.setdefault(key, val)
    except Exception:
        pass


_load_env_file(ROOT_DIR / ".env")


def required(name: str) -> str:
    """Get required environment variable."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def extract_json(result: Any) -> dict:
    """Extract JSON object from MCP tool result."""
    if isinstance(result, dict):
        return result
    try:
        content = getattr(result, "content", None) or result.get("content")
        if isinstance(content, list) and content:
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
    try:
        return json.loads(str(result))
    except Exception:
        return {}


async def find_orphaned_pages(session: ClientSession, confluence_space: str, 
                             date_pattern: str = "20250820") -> List[Dict[str, Any]]:
    """Find pages with the date pattern in their title."""
    print(f"Searching for pages with '{date_pattern}' in title in space {confluence_space}...")
    
    # Use the working query format - quotes around space key are required for personal spaces
    # Get all pages from the space first, then filter by pattern
    cql = f"space = \"{confluence_space}\""
    
    try:
        print(f"Searching space {confluence_space} for all pages...")
        search_result = await session.call_tool(
            "confluence_search_search", 
            {"query": cql, "limit": 50}
        )
        
        search_obj = extract_json(search_result)
        all_pages = search_obj if isinstance(search_obj, list) else search_obj.get("results", [])
        
        print(f"Found {len(all_pages)} total pages in space")
        
        # Filter pages that contain the date pattern in title
        matching_pages = []
        for page in all_pages:
            title = page.get("title", "")
            if date_pattern in title:
                matching_pages.append(page)
                print(f"  - Found matching page: '{title}'")
        
        print(f"Found {len(matching_pages)} pages matching pattern '{date_pattern}'")
        return matching_pages
        
    except Exception as e:
        print(f"Error searching for pages: {e}")
        import traceback
        traceback.print_exc()
        return []


async def delete_pages(session: ClientSession, pages: List[Dict[str, Any]]) -> Dict[str, int]:
    """Delete the found pages."""
    stats = {"deleted": 0, "errors": 0, "skipped": 0}
    
    for page in pages:
        page_id = page.get("id") or page.get("page_id")
        title = page.get("title", "Unknown")
        
        if not page_id:
            print(f"Skipping page '{title}' - no page ID found")
            stats["skipped"] += 1
            continue
            
        try:
            print(f"Deleting page: '{title}' (ID: {page_id})")
            await session.call_tool(
                "confluence_pages_delete_page", 
                {"page_id": str(page_id)}
            )
            stats["deleted"] += 1
            print(f"✓ Deleted page: '{title}'")
            
        except Exception as e:
            error_msg = str(e).lower()
            if "not found" in error_msg or "does not exist" in error_msg:
                print(f"- Page '{title}' already deleted or doesn't exist")
                stats["skipped"] += 1
            else:
                print(f"✗ Failed to delete page '{title}': {e}")
                stats["errors"] += 1
    
    return stats


async def main() -> None:
    """Main cleanup function."""
    print("=== E2E Test Orphaned Pages Cleanup ===")
    
    mcp_url = os.getenv("MCP_URL", "http://localhost:9001/mcp")
    confluence_space = required("CONFLUENCE_SPACE")
    
    # Optional auth headers for multi-tenant server
    headers: dict[str, str] = {}
    if os.getenv("USER_OAUTH_TOKEN"):
        headers["Authorization"] = f"Bearer {os.getenv('USER_OAUTH_TOKEN')}"
    if os.getenv("USER_CLOUD_ID"):
        headers["X-Atlassian-Cloud-Id"] = os.getenv("USER_CLOUD_ID", "")
    
    print(f"Connecting to MCP server at {mcp_url}")
    print(f"Confluence space: {confluence_space}")
    
    async with streamablehttp_client(mcp_url, headers=headers) as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            
            # Find orphaned pages
            orphaned_pages = await find_orphaned_pages(session, confluence_space)
            
            if not orphaned_pages:
                print("No orphaned pages found. Cleanup complete.")
                return
            
            print(f"\nFound {len(orphaned_pages)} orphaned pages:")
            for page in orphaned_pages:
                title = page.get("title", "Unknown")
                page_id = page.get("id") or page.get("page_id", "Unknown")
                print(f"  - '{title}' (ID: {page_id})")
            
            # Confirm deletion
            auto_confirm = os.getenv("AUTO_CONFIRM", "").lower() in ["y", "yes", "true", "1"]
            if auto_confirm:
                print(f"\nAuto-confirming deletion of {len(orphaned_pages)} pages...")
                response = 'y'
            else:
                try:
                    print(f"\nThis will delete {len(orphaned_pages)} pages. Continue? (y/N): ", end="")
                    response = input().strip().lower()
                except (EOFError, KeyboardInterrupt):
                    print("\nUser input not available. Use AUTO_CONFIRM=y to proceed automatically.")
                    return
            
            if response != 'y':
                print("Cleanup cancelled.")
                return
            
            # Delete pages
            print(f"\nDeleting {len(orphaned_pages)} pages...")
            stats = await delete_pages(session, orphaned_pages)
            
            print(f"\n=== Cleanup Summary ===")
            print(f"Pages deleted: {stats['deleted']}")
            print(f"Pages skipped: {stats['skipped']}")
            print(f"Errors: {stats['errors']}")
            
            if stats["deleted"] > 0:
                print("✓ Orphaned pages cleanup completed successfully!")
            elif stats["skipped"] > 0:
                print("- All pages were already deleted or didn't exist")
            else:
                print("✗ No pages were deleted")


if __name__ == "__main__":
    asyncio.run(main())