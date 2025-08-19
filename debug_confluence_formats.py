#!/usr/bin/env python3

import json
import os

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_confluence_formats():
    """Test different content formats."""

    # Get credentials
    email = os.getenv("ATLASSIAN_EMAIL")
    token = os.getenv("ATLASSIAN_API_TOKEN")
    base_url = "https://baseball.atlassian.net/wiki"
    space_id = "655361"

    if not email or not token:
        print("Missing ATLASSIAN_EMAIL or ATLASSIAN_API_TOKEN")
        return

    # Headers
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Atlassian-Token": "no-check",
    }

    # Test 1: Try wiki markup
    print("=== Test 1: Wiki markup ===")
    payload1 = {
        "spaceId": space_id,
        "status": "current",
        "title": "Debug Test Wiki Markup",
        "body": {
            "representation": "wiki",
            "value": "h1. Test Heading\n\nSimple text content.",
        },
    }

    url = f"{base_url}/api/v2/pages"
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload1, indent=2)}")

    response = requests.post(url, json=payload1, headers=headers, auth=(email, token))

    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    print()

    # Test 2: Try storage format
    print("=== Test 2: Storage format ===")
    payload2 = {
        "spaceId": space_id,
        "status": "current",
        "title": "Debug Test Storage",
        "body": {
            "representation": "storage",
            "value": "<h1>Test Heading</h1><p>Simple text content.</p>",
        },
    }

    print(f"Payload: {json.dumps(payload2, indent=2)}")

    response = requests.post(url, json=payload2, headers=headers, auth=(email, token))

    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    print()

    # Test 3: Check if we can get existing pages to see expected format
    print("=== Test 3: Get existing pages ===")
    get_url = f"{base_url}/api/v2/pages?space-id={space_id}&limit=1"
    response = requests.get(get_url, headers=headers, auth=(email, token))
    print(f"GET {get_url}")
    print(f"Status: {response.status_code}")
    if response.ok:
        data = response.json()
        print(f"Response structure: {list(data.keys())}")
        if "results" in data and data["results"]:
            page = data["results"][0]
            print(f"First page keys: {list(page.keys())}")
            if "body" in page:
                print(f"Body structure: {page['body']}")
    else:
        print(f"Error: {response.text}")


if __name__ == "__main__":
    test_confluence_formats()
