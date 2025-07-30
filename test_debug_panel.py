#!/usr/bin/env python3
"""Debug panel parsing."""

import re
from src.mcp_atlassian.formatting.adf_plugins import PanelPlugin

plugin = PanelPlugin()
pattern = plugin.block_pattern

text = """:::panel type="info"
This is an information panel.
:::"""

match = pattern.search(text)
if match:
    print(f"Match found: {match.groups()}")
    data = plugin.parse_block(match, text)
    print(f"Parsed data: {data}")
    
    # Mock render function
    def mock_render(content):
        return [{"type": "text", "text": content}]
    
    node = plugin.render_block(data, mock_render)
    print(f"Rendered node: {node}")
else:
    print("No match found")