#!/usr/bin/env python3

import json
import os

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_confluence_v2_simple():
    """Test Confluence v2 API with very simple content."""

    # Get credentials
    email = os.getenv("ATLASSIAN_EMAIL")
    token = os.getenv("ATLASSIAN_API_TOKEN")
    base_url = "https://baseball.atlassian.net/wiki"
    space_id = "655361"

    if not email or not token:
        print("Missing ATLASSIAN_EMAIL or ATLASSIAN_API_TOKEN")
        return

    # Simple ADF content - just a paragraph
    simple_adf = {
        "version": 1,
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": "Simple test content"}],
            }
        ],
    }

    # Request payload
    payload = {
        "spaceId": space_id,
        "status": "current",
        "title": "Debug Test Page Simple",
        "body": {"representation": "atlas_doc_format", "value": simple_adf},
    }

    # Headers
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Atlassian-Token": "no-check",
    }

    # Make request
    url = f"{base_url}/api/v2/pages"
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    response = requests.post(url, json=payload, headers=headers, auth=(email, token))

    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Response: {response.text}")

    if response.ok:
        print("✅ Success!")
        result = response.json()
        page_id = result.get("id")
        if page_id:
            # Clean up by deleting the test page
            delete_url = f"{base_url}/api/v2/pages/{page_id}"
            delete_response = requests.delete(
                delete_url, headers=headers, auth=(email, token)
            )
            print(f"Cleanup delete: {delete_response.status_code}")
    else:
        print("❌ Failed!")


if __name__ == "__main__":
    test_confluence_v2_simple()
