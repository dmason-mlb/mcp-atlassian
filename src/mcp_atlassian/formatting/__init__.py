"""Formatting modules for converting between different text formats.

This package provides formatters for converting markdown to various Atlassian formats:
- ADF (Atlassian Document Format) for Cloud instances
- Wiki markup for Server/Data Center instances
"""

from .adf import ADFGenerator
from .router import FormatRouter

__all__ = ["ADFGenerator", "FormatRouter"]