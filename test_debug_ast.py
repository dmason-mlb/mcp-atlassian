#!/usr/bin/env python3
"""Debug AST generator."""

import logging
logging.basicConfig(level=logging.DEBUG)

from src.mcp_atlassian.formatting.adf_ast import ASTBasedADFGenerator

generator = ASTBasedADFGenerator()

markdown = """:::panel type="info"
This is an information panel.
:::"""

try:
    result = generator.markdown_to_adf(markdown)
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()