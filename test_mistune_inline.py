#!/usr/bin/env python3
"""Test mistune inline parser."""

import mistune

# Create a markdown instance
md = mistune.create_markdown()

# Get the inline parser
print(f"Markdown inline attribute: {hasattr(md, 'inline')}")
print(f"Markdown _inline_parser attribute: {hasattr(md, '_inline_parser')}")

# Try to parse inline content
text = "This is **bold** text"
try:
    # Method 1: Direct parse
    parser = mistune.InlineParser()
    tokens = parser.parse(text)
    print(f"Direct parse tokens: {tokens}")
except Exception as e:
    print(f"Direct parse error: {e}")

# Method 2: Through markdown instance  
try:
    if hasattr(md, 'inline'):
        tokens = md.inline(text)
        print(f"Markdown inline tokens: {tokens}")
except Exception as e:
    print(f"Markdown inline error: {e}")

# Check mistune version
import mistune
print(f"\nMistune version: {mistune.__version__}")