#!/usr/bin/env python3
"""Test simple mistune block plugin."""

import mistune
import re

class DebugRenderer(mistune.BaseRenderer):
    def render_token(self, token, state):
        print(f"Token: type={token.get('type')}, raw={repr(token.get('raw', '')[:50])}")
        return {"type": token['type'], "raw": token.get('raw', '')}
    
    def __call__(self, tokens, state):
        token_list = list(tokens)
        print(f"Total tokens: {len(token_list)}")
        for i, token in enumerate(token_list):
            print(f"  Token {i}: {token}")
        return {"tokens": token_list}

def simple_plugin(md):
    """Simple test plugin."""
    def parse_simple(self, m, state):
        print(f"parse_simple called! Match: {m.group(0)}")
        state.append_token({
            'type': 'simple_block',
            'raw': m.group(0)
        })
        return m.end()
    
    # Register with a simple pattern
    md.block.register(
        'simple_block',
        r'^:::test\n.*?\n:::',
        parse_simple
    )

# Test
renderer = DebugRenderer()
md = mistune.create_markdown(renderer=renderer, plugins=[simple_plugin])

text = """:::test
Hello world
:::"""

print("Testing mistune plugin...")
result = md(text)
print(f"Result: {result}")