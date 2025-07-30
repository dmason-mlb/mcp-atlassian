#!/usr/bin/env python3
"""Test regex pattern."""

import re

pattern = r'^:::([a-z]+)(?:\s+([^\n]+))?\n((?:.*?\n)*?)^:::[ \t]*$'

text = """:::panel type="info"
This is an information panel.
:::"""

# Test with MULTILINE
match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
print(f"Match with MULTILINE|DOTALL: {match}")
if match:
    print(f"Groups: {match.groups()}")

# Test the panel plugin pattern
panel_pattern = re.compile(
    r'^:::panel(?:\s+type="(info|note|warning|success|error)")?\s*\n'
    r'(.*?)\n'
    r'^:::$',
    re.MULTILINE | re.DOTALL
)

match2 = panel_pattern.search(text)
print(f"\nPanel plugin match: {match2}")
if match2:
    print(f"Groups: {match2.groups()}")