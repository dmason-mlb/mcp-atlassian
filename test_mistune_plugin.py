#!/usr/bin/env python3
"""Test mistune plugin pattern."""

import mistune

def my_plugin(md):
    """Example mistune plugin."""
    def parse_my_block(m, state):
        """Parser for custom block."""
        print(f"parse_my_block called with match groups: {m.groups()}")
        return {'type': 'my_block', 'raw': m.group(0)}
    
    # Register the pattern
    md.block.register(
        'my_block',
        r'^:::test\n(.*?)\n:::$',
        parse_my_block,
        before='fenced_code'
    )

# Create markdown instance
md = mistune.create_markdown(plugins=[my_plugin])

# Test it
text = """:::test
Hello world
:::"""

print("Testing mistune plugin pattern...")
try:
    result = md(text)
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()