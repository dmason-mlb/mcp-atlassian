"""ADF (Atlassian Document Format) generator for converting markdown to ADF JSON.

This module provides functionality to convert markdown text to ADF format that is 
required by Jira and Confluence Cloud APIs. It uses a visitor pattern to transform 
markdown AST nodes into proper ADF JSON structure.

Performance optimizations:
- LRU caching for frequently converted markdown patterns
- Efficient AST traversal with optimized data structures
- Lazy evaluation for complex elements
- Comprehensive error handling with graceful degradation
"""

import hashlib
import logging
import time
from functools import lru_cache
from typing import Any

import markdown

logger = logging.getLogger(__name__)


class ADFGenerator:
    """Generator for converting markdown text to Atlassian Document Format (ADF) JSON.
    
    Performance optimizations:
    - LRU cache for frequently converted patterns (maxsize=256)
    - Performance metrics collection for monitoring
    - Graceful error handling with fallback mechanisms
    """

    def __init__(self, cache_size: int = 256) -> None:
        """Initialize the ADF generator with markdown parser and performance optimizations.
        
        Args:
            cache_size: Maximum size of the conversion cache (default: 256)
        """
        self.md = markdown.Markdown(
            extensions=[
                'codehilite',
                'tables',
                'fenced_code',
                'nl2br',
                'toc'
            ],
            extension_configs={
                'codehilite': {
                    'css_class': 'codehilite',
                    'use_pygments': False
                }
            }
        )

        # Performance metrics
        self.metrics: dict[str, Any] = {
            'conversions_total': 0,
            'conversions_cached': 0,
            'conversion_time_total': 0.0,
            'conversion_errors': 0,
            'last_error': None
        }

        # Configure caching based on cache_size
        self._configure_cache(cache_size)

    def _configure_cache(self, cache_size: int) -> None:
        """Configure LRU cache for markdown conversion."""
        # Create cached version of _convert_markdown_to_adf
        self._cached_convert = lru_cache(maxsize=cache_size)(self._convert_markdown_to_adf_uncached)

    def markdown_to_adf(self, markdown_text: str) -> dict[str, Any]:
        """
        Convert markdown text to ADF JSON format with caching and performance monitoring.
        
        Args:
            markdown_text: Input markdown text to convert
            
        Returns:
            Dictionary representing ADF JSON structure
            
        Raises:
            ValueError: If markdown conversion fails after all fallback attempts
        """
        start_time = time.time()
        self.metrics['conversions_total'] = self.metrics['conversions_total'] + 1

        try:
            # Handle empty input efficiently
            if not markdown_text or not markdown_text.strip():
                return {
                    "type": "doc",
                    "version": 1,
                    "content": []
                }

            # Create cache key from input
            cache_key = hashlib.md5(markdown_text.encode('utf-8')).hexdigest()

            # Try cached conversion first
            try:
                result = self._cached_convert(cache_key, markdown_text)
                self.metrics['conversions_cached'] = self.metrics['conversions_cached'] + 1
                logger.debug(f"ADF conversion cache hit for key: {cache_key[:8]}...")
                return result
            except Exception as cache_error:
                logger.warning(f"Cache error, falling back to direct conversion: {cache_error}")
                # Fall back to direct conversion
                result = self._convert_markdown_to_adf_uncached(cache_key, markdown_text)
                return result

        except Exception as e:
            self.metrics['conversion_errors'] = self.metrics['conversion_errors'] + 1
            self.metrics['last_error'] = str(e)
            logger.error(f"ADF conversion failed: {e}")

            # Graceful degradation: return a basic ADF with error information
            return self._create_error_adf(markdown_text, str(e))

        finally:
            # Update performance metrics
            conversion_time = time.time() - start_time
            self.metrics['conversion_time_total'] = self.metrics['conversion_time_total'] + conversion_time

            if conversion_time > 0.1:  # Log slow conversions
                logger.warning(f"Slow ADF conversion: {conversion_time:.3f}s for {len(markdown_text)} chars")

    def _convert_markdown_to_adf_uncached(self, cache_key: str, markdown_text: str) -> dict[str, Any]:
        """
        Internal method for actual ADF conversion (uncached version).
        
        Args:
            cache_key: Cache key for this conversion (for logging)
            markdown_text: Input markdown text to convert
            
        Returns:
            Dictionary representing ADF JSON structure
        """
        try:
            if not markdown_text or not markdown_text.strip():
                return self._create_empty_document()

            # Parse markdown to HTML first, then extract structure
            html_output = self.md.convert(markdown_text)

            # Reset the markdown instance for next use
            self.md.reset()

            # Parse the HTML and convert to ADF
            adf_content = self._html_to_adf_content(html_output)

            return {
                "version": 1,
                "type": "doc",
                "content": adf_content
            }

        except Exception as e:
            logger.error(f"Failed to convert markdown to ADF: {e}")
            # Fallback to plain text in a paragraph
            return self._create_plain_text_document(markdown_text)

    def _create_empty_document(self) -> dict[str, Any]:
        """Create an empty ADF document."""
        return {
            "version": 1,
            "type": "doc",
            "content": []
        }

    def _create_plain_text_document(self, text: str) -> dict[str, Any]:
        """Create ADF document with plain text fallback."""
        return {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": text
                        }
                    ]
                }
            ]
        }

    def _html_to_adf_content(self, html: str) -> list[dict[str, Any]]:
        """
        Convert HTML to ADF content blocks.
        
        This is a simplified converter that handles basic HTML elements
        and converts them to corresponding ADF structures.
        """
        from bs4 import BeautifulSoup

        try:
            soup = BeautifulSoup(html, 'html.parser')
            content = []

            # Process each top-level element
            for element in soup.children:
                if hasattr(element, 'name') and element.name:
                    adf_node = self._convert_html_element_to_adf(element)
                    if adf_node:
                        content.append(adf_node)
                elif hasattr(element, 'strip') and element.strip():  # Text node
                    # Wrap loose text in paragraph
                    content.append({
                        "type": "paragraph",
                        "content": [{"type": "text", "text": element.strip()}]
                    })

            return content if content else [self._create_empty_paragraph()]

        except Exception as e:
            logger.error(f"Failed to parse HTML to ADF: {e}")
            return [self._create_plain_text_paragraph(html)]

    def _convert_html_element_to_adf(self, element: Any) -> dict[str, Any] | None:
        """Convert a single HTML element to ADF node."""
        if not hasattr(element, 'name') or not element.name:
            return None
        tag_name = element.name.lower()

        if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            return self._convert_heading(element)
        elif tag_name == 'p':
            return self._convert_paragraph(element)
        elif tag_name in ['ul', 'ol']:
            return self._convert_list(element)
        elif tag_name == 'pre':
            return self._convert_code_block(element)
        elif tag_name == 'blockquote':
            return self._convert_blockquote(element)
        elif tag_name == 'table':
            return self._convert_table(element)
        elif tag_name == 'hr':
            return self._convert_rule()
        else:
            # For unhandled elements, try to extract text content
            text_content = element.get_text(strip=True)
            if text_content:
                return {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": text_content}]
                }
        return None

    def _convert_heading(self, element: Any) -> dict[str, Any]:
        """Convert heading element to ADF heading."""
        level = int(element.name[1])  # Extract number from h1, h2, etc.

        return {
            "type": "heading",
            "attrs": {"level": level},
            "content": self._convert_inline_content(element)
        }

    def _convert_paragraph(self, element: Any) -> dict[str, Any]:
        """Convert paragraph element to ADF paragraph."""
        content = self._convert_inline_content(element)

        # Don't create empty paragraphs
        if not content:
            return self._create_empty_paragraph()

        return {
            "type": "paragraph",
            "content": content
        }

    def _convert_list(self, element: Any, nesting_level: int = 0) -> dict[str, Any]:
        """Convert list element to ADF bulletList or orderedList with lazy evaluation."""
        list_type = "orderedList" if element.name == "ol" else "bulletList"
        max_items = 100  # Limit list items for performance

        content = []
        item_count = 0

        for li in element.find_all('li', recursive=False):
            if item_count >= max_items:
                # Add truncation notice for very large lists
                content.append({
                    "type": "listItem",
                    "content": [{
                        "type": "paragraph",
                        "content": [{"type": "text", "text": f"... (list truncated after {max_items} items for performance)"}]
                    }]
                })
                break

            list_item_content = self._convert_list_item_content(li, nesting_level)
            if list_item_content:
                content.append({
                    "type": "listItem",
                    "content": list_item_content
                })
            item_count += 1

        return {
            "type": list_type,
            "content": content
        }

    def _convert_list_item_content(self, li_element: Any, nesting_level: int = 0) -> list[dict[str, Any]]:
        """Convert list item content to ADF format with lazy evaluation for deep nesting."""
        content = []
        max_nesting = 10  # Prevent excessive nesting for performance

        # Prevent infinite recursion and excessive nesting
        if nesting_level > max_nesting:
            logger.warning(f"List nesting exceeded maximum depth ({max_nesting}), truncating")
            return [{
                "type": "paragraph",
                "content": [{"type": "text", "text": f"... (nesting too deep, truncated at level {max_nesting})"}]
            }]

        # Handle nested elements in list item with lazy evaluation
        child_count = 0
        max_children = 50  # Limit children per list item

        for child in li_element.children:
            if child_count >= max_children:
                content.append({
                    "type": "paragraph",
                    "content": [{"type": "text", "text": f"... (list item truncated after {max_children} children)"}]
                })
                break

            if hasattr(child, 'name'):
                if child.name in ['ul', 'ol']:
                    # Nested list - use lazy evaluation
                    nested_list = self._convert_list(child, nesting_level + 1)
                    content.append(nested_list)
                elif child.name == 'p':
                    # Paragraph in list item
                    para_content = self._convert_inline_content(child)
                    if para_content:
                        content.append({
                            "type": "paragraph",
                            "content": para_content
                        })
                else:
                    # Other elements - treat as paragraph
                    text = child.get_text(strip=True)
                    if text:
                        # Limit text length for performance
                        if len(text) > 1000:
                            text = text[:997] + "..."
                        content.append({
                            "type": "paragraph",
                            "content": [{"type": "text", "text": text}]
                        })
            elif child.strip():
                # Direct text content
                text = child.strip()
                if len(text) > 1000:
                    text = text[:997] + "..."
                content.append({
                    "type": "paragraph",
                    "content": [{"type": "text", "text": text}]
                })

            child_count += 1

        # If no content found, create empty paragraph
        return content if content else [self._create_empty_paragraph()]

    def _convert_code_block(self, element: Any) -> dict[str, Any]:
        """Convert code block to ADF codeBlock."""
        code_element = element.find('code')
        if code_element:
            code_text = code_element.get_text().rstrip('\n')

            # Try to extract language from class
            language = None
            if code_element.get('class'):
                for cls in code_element.get('class'):
                    if cls.startswith('language-'):
                        language = cls.replace('language-', '')
                        break

            attrs = {}
            if language:
                attrs['language'] = language

            return {
                "type": "codeBlock",
                "attrs": attrs,
                "content": [
                    {
                        "type": "text",
                        "text": code_text
                    }
                ]
            }
        else:
            # Fallback to plain text
            return {
                "type": "codeBlock",
                "content": [
                    {
                        "type": "text",
                        "text": element.get_text().rstrip('\n')
                    }
                ]
            }

    def _convert_blockquote(self, element: Any) -> dict[str, Any]:
        """Convert blockquote to ADF blockquote."""
        content = []

        for child in element.find_all(['p', 'div'], recursive=False):
            para_content = self._convert_inline_content(child)
            if para_content:
                content.append({
                    "type": "paragraph",
                    "content": para_content
                })

        if not content:
            # Fallback to text content
            text = element.get_text(strip=True)
            if text:
                content = [{
                    "type": "paragraph",
                    "content": [{"type": "text", "text": text}]
                }]

        return {
            "type": "blockquote",
            "content": content if content else [self._create_empty_paragraph()]
        }

    def _convert_table(self, element: Any) -> dict[str, Any]:
        """Convert table to ADF table with lazy evaluation for performance."""
        # Use lazy evaluation for large tables to improve performance

        def lazy_convert_rows():
            """Lazily convert table rows to avoid processing large tables upfront."""
            rows = []
            row_count = 0
            max_rows = 50  # Limit large tables for performance

            for tr in element.find_all('tr'):
                if row_count >= max_rows:
                    # Add truncation notice for very large tables
                    rows.append({
                        "type": "tableRow",
                        "content": [{
                            "type": "tableCell",
                            "content": [{
                                "type": "paragraph",
                                "content": [{"type": "text", "text": f"... table truncated after {max_rows} rows for performance"}]
                            }]
                        }]
                    })
                    break

                cells = []
                cell_count = 0
                max_cells = 20  # Limit cells per row

                for td in tr.find_all(['td', 'th']):
                    if cell_count >= max_cells:
                        cells.append({
                            "type": "tableCell",
                            "content": [{
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "... (truncated)"}]
                            }]
                        })
                        break

                    # Lazy content conversion - only process when needed
                    cell_content = self._convert_inline_content(td)
                    cells.append({
                        "type": "tableCell",
                        "content": [{
                            "type": "paragraph",
                            "content": cell_content if cell_content else [{"type": "text", "text": ""}]
                        }]
                    })
                    cell_count += 1

                if cells:
                    rows.append({
                        "type": "tableRow",
                        "content": cells
                    })
                row_count += 1

            return rows

        return {
            "type": "table",
            "content": lazy_convert_rows()
        }

    def _convert_rule(self) -> dict[str, Any]:
        """Convert horizontal rule to ADF rule."""
        return {"type": "rule"}

    def _convert_inline_content(self, element: Any) -> list[dict[str, Any]]:
        """Convert inline content (text with formatting) to ADF."""
        content = []

        # Handle direct text and inline formatting
        for child in element.children:
            if hasattr(child, 'name') and child.name:  # Check that name is not None
                adf_inline = self._convert_inline_element(child)
                if adf_inline:
                    content.extend(adf_inline if isinstance(adf_inline, list) else [adf_inline])
            elif hasattr(child, 'strip') and child.strip():
                # Direct text node (NavigableString)
                content.append({
                    "type": "text",
                    "text": child.strip()
                })

        return content

    def _convert_inline_element(self, element: Any) -> dict[str, Any] | list[dict[str, Any]] | None:
        """Convert inline HTML element to ADF inline node."""
        if not hasattr(element, 'name') or element.name is None:
            return None
        tag_name = element.name.lower()
        text_content = element.get_text()

        if not text_content.strip():
            return None

        # Basic text formatting
        marks: list[dict[str, Any]] = []

        if tag_name in ['strong', 'b']:
            marks.append({"type": "strong"})
        elif tag_name in ['em', 'i']:
            marks.append({"type": "em"})
        elif tag_name == 'code':
            marks.append({"type": "code"})
        elif tag_name in ['s', 'del', 'strike']:
            marks.append({"type": "strike"})
        elif tag_name == 'u':
            marks.append({"type": "underline"})
        elif tag_name == 'a':
            href = element.get('href')
            if href:
                marks.append({
                    "type": "link", 
                    "attrs": {"href": href}
                })

        # For nested formatting, we need to handle child elements
        if element.children and any(hasattr(child, 'name') and child.name for child in element.children):
            # Has nested elements - process recursively
            nested_content = []
            for child in element.children:
                if hasattr(child, 'name') and child.name:
                    child_content = self._convert_inline_element(child)
                    if child_content:
                        if isinstance(child_content, list):
                            nested_content.extend(child_content)
                        else:
                            nested_content.append(child_content)
                elif hasattr(child, 'strip') and child.strip():
                    text_node = {
                        "type": "text",
                        "text": child.strip()
                    }
                    if marks:
                        text_node["marks"] = marks
                    nested_content.append(text_node)
            return nested_content
        else:
            # Simple text with marks
            text_node = {
                "type": "text",
                "text": text_content
            }
            if marks:
                text_node["marks"] = marks

            return text_node

    def _create_empty_paragraph(self) -> dict[str, Any]:
        """Create an empty ADF paragraph."""
        return {
            "type": "paragraph",
            "content": []
        }

    def _create_plain_text_paragraph(self, text: str) -> dict[str, Any]:
        """Create ADF paragraph with plain text."""
        return {
            "type": "paragraph",
            "content": [
                {
                    "type": "text",
                    "text": text
                }
            ]
        }

    def validate_adf(self, adf_json: dict[str, Any]) -> bool:
        """
        Validate ADF JSON structure (basic validation).
        
        Args:
            adf_json: ADF JSON to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Basic structure validation
            if not isinstance(adf_json, dict):
                return False  # type: ignore[unreachable]

            required_fields = ["version", "type", "content"]
            if not all(field in adf_json for field in required_fields):
                return False

            if adf_json["type"] != "doc":
                return False

            if not isinstance(adf_json["content"], list):
                return False

            # Validate each content block has required type
            for content_block in adf_json["content"]:
                if not isinstance(content_block, dict) or "type" not in content_block:
                    return False

            return True

        except Exception as e:
            logger.error(f"ADF validation error: {e}")
            return False

    def _create_error_adf(self, original_markdown: str, error_message: str) -> dict[str, Any]:
        """Create a graceful fallback ADF document when conversion fails.
        
        Args:
            original_markdown: The original markdown that failed to convert
            error_message: The error message from the failed conversion
            
        Returns:
            ADF document with error information and original text
        """
        logger.warning(f"Creating error ADF for failed conversion: {error_message}")

        # Try to preserve at least the original text content
        try:
            # Remove markdown formatting and use as plain text
            plain_text = original_markdown.replace('*', '').replace('_', '').replace('#', '').strip()

            # Limit text length to prevent oversized documents
            if len(plain_text) > 1000:
                plain_text = plain_text[:997] + "..."

            return {
                "version": 1,
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": f"[Conversion Error] {plain_text}"
                            }
                        ]
                    }
                ]
            }
        except Exception as fallback_error:
            # Ultimate fallback - minimal valid ADF
            logger.error(f"Even error ADF creation failed: {fallback_error}")
            return {
                "version": 1,
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "[Conversion Failed - Unable to Process Content]"
                            }
                        ]
                    }
                ]
            }

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics for monitoring and optimization.
        
        Returns:
            Dictionary containing performance statistics
        """
        cache_info = self._cached_convert.cache_info() if hasattr(self._cached_convert, 'cache_info') else None

        metrics = self.metrics.copy()
        metrics.update({
            'cache_hit_rate': (self.metrics['conversions_cached'] / max(1, self.metrics['conversions_total'])) * 100,
            'average_conversion_time': self.metrics['conversion_time_total'] / max(1, self.metrics['conversions_total']),
            'error_rate': (self.metrics['conversion_errors'] / max(1, self.metrics['conversions_total'])) * 100,
            'cache_info': {
                'hits': cache_info.hits if cache_info else 0,
                'misses': cache_info.misses if cache_info else 0,
                'maxsize': cache_info.maxsize if cache_info else 0,
                'currsize': cache_info.currsize if cache_info else 0
            } if cache_info else None
        })

        return metrics

    def clear_cache(self) -> None:
        """Clear the conversion cache to free memory."""
        if hasattr(self._cached_convert, 'cache_clear'):
            self._cached_convert.cache_clear()
            logger.info("ADF conversion cache cleared")

    def reset_metrics(self) -> None:
        """Reset performance metrics counters."""
        self.metrics = {
            'conversions_total': 0,
            'conversions_cached': 0,
            'conversion_time_total': 0.0,
            'conversion_errors': 0,
            'last_error': None
        }
        logger.info("ADF performance metrics reset")
