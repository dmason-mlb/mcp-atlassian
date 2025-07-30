#!/usr/bin/env python3
"""Test mistune pattern matching."""

import re

# Test the pattern from adf_extensions
pattern = r'^:::([a-z]+)(?:\s+([^\n]+))?\n((?:.*?\n)*?)^:::[ \t]*$'

text = """:::panel type="info"
This is an information panel.
:::"""

# Test with different flags
print("Testing pattern...")
match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
if match:
    print(f"Match found with MULTILINE|DOTALL: {match.groups()}")
else:
    print("No match with MULTILINE|DOTALL")

# Test without anchors
pattern2 = r':::([a-z]+)(?:\s+([^\n]+))?\n((?:.*?\n)*?):::'
match2 = re.search(pattern2, text, re.DOTALL)
if match2:
    print(f"Match found without anchors: {match2.groups()}")

# Test the exact text mistune would see
lines = text.strip().split('\n')
for i, line in enumerate(lines):
    print(f"Line {i}: repr={repr(line)}")