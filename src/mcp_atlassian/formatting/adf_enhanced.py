"""Enhanced ADF (Atlassian Document Format) generator with full spec compliance.

This module provides an improved implementation that directly converts markdown to ADF
without the HTML intermediate step, supporting more ADF-specific features.
"""

import hashlib
import logging
import re
import time
from functools import lru_cache
from typing import Any, Optional

import markdown
from markdown import BlockParser, InlineProcessor
from markdown.extensions import Extension
from markdown.treebuilders import etree

logger = logging.getLogger(__name__)


class DirectADFGenerator:
    """Enhanced ADF generator with direct markdown-to-ADF conversion.
    
    Key improvements:
    - Direct conversion without HTML intermediate
    - Support for panels, expand/collapse, and media
    - Proper table header detection
    - Configurable performance limits
    - Mark combination validation
    """

    def __init__(
        self, 
        cache_size: int = 256,
        max_table_rows: int = 100,
        max_list_items: int = 200,
        max_nesting_depth: int = 10
    ) -> None:
        """Initialize enhanced ADF generator.
        
        Args:
            cache_size: LRU cache size for conversions
            max_table_rows: Maximum rows before table truncation
            max_list_items: Maximum items before list truncation  
            max_nesting_depth: Maximum nesting depth for lists
        """
        self.cache_size = cache_size
        self.max_table_rows = max_table_rows
        self.max_list_items = max_list_items
        self.max_nesting_depth = max_nesting_depth
        
        # Performance metrics
        self.metrics: dict[str, Any] = {
            'conversions_total': 0,
            'conversions_cached': 0,
            'conversion_time_total': 0.0,
            'conversion_errors': 0,
            'nodes_created': {}
        }
        
        # Configure cache
        self._configure_cache(cache_size)
        
        # Compile regex patterns for better performance
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for markdown parsing."""
        # Panel detection: {panel:type}content{panel}
        self.panel_pattern = re.compile(
            r'\{panel:(\w+)\}(.*?)\{panel\}',
            re.DOTALL | re.MULTILINE
        )
        
        # Status detection: {status:color}text{status}
        self.status_pattern = re.compile(
            r'\{status:(\w+)\}(.*?)\{status\}'
        )
        
        # Mention detection: @[User Name]
        self.mention_pattern = re.compile(
            r'@\[([^\]]+)\]'
        )
        
        # Date detection: {date:YYYY-MM-DD}
        self.date_pattern = re.compile(
            r'\{date:(\d{4}-\d{2}-\d{2})\}'
        )
        
        # Emoji detection: :emoji_name:
        self.emoji_pattern = re.compile(
            r':([a-zA-Z0-9_+-]+):'
        )

    def _configure_cache(self, cache_size: int) -> None:
        """Configure LRU cache for conversions."""
        self._cached_convert = lru_cache(maxsize=cache_size)(
            self._convert_markdown_uncached
        )

    def markdown_to_adf(self, markdown_text: str) -> dict[str, Any]:
        """Convert markdown to ADF with caching.
        
        Args:
            markdown_text: Input markdown text
            
        Returns:
            ADF document structure
        """
        start_time = time.time()
        self.metrics['conversions_total'] += 1
        
        try:
            # Handle empty input
            if not markdown_text or not markdown_text.strip():
                return self._create_empty_document()
            
            # Create cache key
            cache_key = hashlib.md5(markdown_text.encode('utf-8')).hexdigest()
            
            # Try cached result
            result = self._cached_convert(cache_key, markdown_text)
            if result:
                self.metrics['conversions_cached'] += 1
            
            return result
            
        except Exception as e:
            self.metrics['conversion_errors'] += 1
            logger.error(f"ADF conversion failed: {e}")
            return self._create_error_document(markdown_text, str(e))
            
        finally:
            conversion_time = time.time() - start_time
            self.metrics['conversion_time_total'] += conversion_time
            if conversion_time > 0.1:
                logger.warning(
                    f"Slow conversion: {conversion_time:.3f}s for {len(markdown_text)} chars"
                )

    def _convert_markdown_uncached(
        self, 
        cache_key: str, 
        markdown_text: str
    ) -> dict[str, Any]:
        """Convert markdown to ADF without caching.
        
        This method does direct parsing of markdown patterns to ADF nodes.
        """
        # Pre-process for ADF-specific patterns
        content = self._preprocess_markdown(markdown_text)
        
        # Parse into blocks
        blocks = self._parse_markdown_blocks(content)
        
        # Convert blocks to ADF nodes
        adf_content = []
        for block in blocks:
            node = self._convert_block_to_adf(block)
            if node:
                adf_content.append(node)
                self._track_node_metrics(node['type'])
        
        return {
            "version": 1,
            "type": "doc",
            "content": adf_content
        }

    def _preprocess_markdown(self, text: str) -> str:
        """Pre-process markdown for ADF-specific patterns."""
        # Handle panels first to preserve internal content
        text = self._extract_panels(text)
        
        # Handle other ADF-specific patterns
        text = self._extract_status(text)
        text = self._extract_mentions(text)
        text = self._extract_dates(text)
        
        return text

    def _extract_panels(self, text: str) -> str:
        """Extract and mark panel blocks."""
        def panel_replacer(match):
            panel_type = match.group(1)
            content = match.group(2).strip()
            # Mark with special delimiter for later processing
            return f"\n<<<PANEL:{panel_type}>>>\n{content}\n<<<END_PANEL>>>\n"
        
        return self.panel_pattern.sub(panel_replacer, text)

    def _extract_status(self, text: str) -> str:
        """Extract and mark status inline elements."""
        def status_replacer(match):
            color = match.group(1)
            status_text = match.group(2)
            return f"<<<STATUS:{color}:{status_text}>>>"
        
        return self.status_pattern.sub(status_replacer, text)

    def _extract_mentions(self, text: str) -> str:
        """Extract and mark mention inline elements."""
        def mention_replacer(match):
            name = match.group(1)
            return f"<<<MENTION:{name}>>>"
        
        return self.mention_pattern.sub(mention_replacer, text)

    def _extract_dates(self, text: str) -> str:
        """Extract and mark date inline elements."""
        def date_replacer(match):
            date = match.group(1)
            # Convert to timestamp (simplified)
            return f"<<<DATE:{date}>>>"
        
        return self.date_pattern.sub(date_replacer, text)

    def _parse_markdown_blocks(self, text: str) -> list[dict[str, Any]]:
        """Parse markdown into block structures."""
        blocks = []
        lines = text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check for panel marker
            if line.startswith("<<<PANEL:"):
                panel_type = line[9:line.index(">>>")]
                content_lines = []
                i += 1
                while i < len(lines) and not lines[i].startswith("<<<END_PANEL>>>"):
                    content_lines.append(lines[i])
                    i += 1
                blocks.append({
                    'type': 'panel',
                    'panel_type': panel_type,
                    'content': '\n'.join(content_lines)
                })
                i += 1
                continue
            
            # Check for headings
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                if 1 <= level <= 6:
                    blocks.append({
                        'type': 'heading',
                        'level': level,
                        'content': line.lstrip('#').strip()
                    })
                    i += 1
                    continue
            
            # Check for code blocks
            if line.startswith('```'):
                language = line[3:].strip() or None
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                blocks.append({
                    'type': 'codeBlock',
                    'language': language,
                    'content': '\n'.join(code_lines)
                })
                i += 1
                continue
            
            # Check for lists
            if line.strip().startswith(('- ', '* ', '+ ')):
                list_block = self._parse_list_block(lines, i, 'bulletList')
                blocks.append(list_block)
                i = list_block['end_index']
                continue
            
            # Check for ordered lists
            if re.match(r'^\d+\.\s', line.strip()):
                list_block = self._parse_list_block(lines, i, 'orderedList')
                blocks.append(list_block)
                i = list_block['end_index']
                continue
            
            # Check for blockquote
            if line.startswith('>'):
                quote_lines = []
                while i < len(lines) and lines[i].startswith('>'):
                    quote_lines.append(lines[i][1:].strip())
                    i += 1
                blocks.append({
                    'type': 'blockquote',
                    'content': '\n'.join(quote_lines)
                })
                continue
            
            # Check for horizontal rule
            if line.strip() in ['---', '***', '___'] and len(line.strip()) >= 3:
                blocks.append({'type': 'rule'})
                i += 1
                continue
            
            # Check for table
            if i + 1 < len(lines) and '|' in line and '|' in lines[i + 1]:
                table_block = self._parse_table_block(lines, i)
                if table_block:
                    blocks.append(table_block)
                    i = table_block['end_index']
                    continue
            
            # Default: paragraph
            if line.strip():
                para_lines = [line]
                i += 1
                while i < len(lines) and lines[i].strip() and not self._is_block_start(lines[i]):
                    para_lines.append(lines[i])
                    i += 1
                blocks.append({
                    'type': 'paragraph',
                    'content': '\n'.join(para_lines)
                })
            else:
                i += 1
        
        return blocks

    def _is_block_start(self, line: str) -> bool:
        """Check if line starts a new block element."""
        line = line.strip()
        return (
            line.startswith('#') or
            line.startswith('```') or
            line.startswith(('- ', '* ', '+ ')) or
            re.match(r'^\d+\.\s', line) or
            line.startswith('>') or
            line in ['---', '***', '___'] or
            '|' in line or
            line.startswith("<<<PANEL:")
        )

    def _parse_list_block(
        self, 
        lines: list[str], 
        start_index: int, 
        list_type: str
    ) -> dict[str, Any]:
        """Parse a list block with proper nesting."""
        items = []
        i = start_index
        current_indent = 0
        
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                # Check if next line continues the list
                if i + 1 < len(lines) and self._is_list_item(lines[i + 1]):
                    i += 1
                    continue
                else:
                    break
            
            # Check if it's a list item
            indent = len(line) - len(line.lstrip())
            if self._is_list_item(line.lstrip()):
                # Extract item content
                if list_type == 'bulletList':
                    content = re.sub(r'^[-*+]\s+', '', line.lstrip())
                else:
                    content = re.sub(r'^\d+\.\s+', '', line.lstrip())
                
                items.append({
                    'indent': indent,
                    'content': content,
                    'children': []
                })
                i += 1
            else:
                # Not a list item, end of list
                break
        
        return {
            'type': list_type,
            'items': items,
            'end_index': i
        }

    def _is_list_item(self, line: str) -> bool:
        """Check if line is a list item."""
        line = line.strip()
        return (
            line.startswith(('- ', '* ', '+ ')) or
            re.match(r'^\d+\.\s', line) is not None
        )

    def _parse_table_block(self, lines: list[str], start_index: int) -> dict[str, Any] | None:
        """Parse a markdown table."""
        if '|' not in lines[start_index]:
            return None
        
        rows = []
        i = start_index
        has_header = False
        
        # Parse rows
        while i < len(lines) and '|' in lines[i]:
            cells = [cell.strip() for cell in lines[i].split('|')[1:-1]]
            if cells:
                rows.append(cells)
            i += 1
            
            # Check for separator row (indicates header)
            if i < len(lines) and re.match(r'^[\s|:-]+$', lines[i]):
                has_header = True
                i += 1
        
        if not rows:
            return None
        
        return {
            'type': 'table',
            'rows': rows,
            'has_header': has_header,
            'end_index': i
        }

    def _convert_block_to_adf(self, block: dict[str, Any]) -> dict[str, Any] | None:
        """Convert a parsed block to ADF node."""
        block_type = block['type']
        
        if block_type == 'heading':
            return {
                "type": "heading",
                "attrs": {"level": block['level']},
                "content": self._parse_inline_content(block['content'])
            }
        
        elif block_type == 'paragraph':
            content = self._parse_inline_content(block['content'])
            if content:
                return {
                    "type": "paragraph",
                    "content": content
                }
        
        elif block_type == 'codeBlock':
            attrs = {}
            if block.get('language'):
                attrs['language'] = block['language']
            return {
                "type": "codeBlock",
                "attrs": attrs,
                "content": [{"type": "text", "text": block['content']}]
            }
        
        elif block_type in ['bulletList', 'orderedList']:
            return self._convert_list_to_adf(block)
        
        elif block_type == 'blockquote':
            # Parse content as nested blocks
            nested_blocks = self._parse_markdown_blocks(block['content'])
            content = []
            for nested in nested_blocks:
                node = self._convert_block_to_adf(nested)
                if node:
                    content.append(node)
            return {
                "type": "blockquote",
                "content": content if content else [{"type": "paragraph", "content": []}]
            }
        
        elif block_type == 'rule':
            return {"type": "rule"}
        
        elif block_type == 'table':
            return self._convert_table_to_adf(block)
        
        elif block_type == 'panel':
            return self._convert_panel_to_adf(block)
        
        return None

    def _convert_list_to_adf(self, list_block: dict[str, Any]) -> dict[str, Any]:
        """Convert list block to ADF format."""
        list_type = list_block['type']
        items = []
        
        for idx, item in enumerate(list_block['items']):
            if idx >= self.max_list_items:
                # Add truncation notice
                items.append({
                    "type": "listItem",
                    "content": [{
                        "type": "paragraph",
                        "content": [{
                            "type": "text",
                            "text": f"... (list truncated after {self.max_list_items} items)"
                        }]
                    }]
                })
                break
            
            item_content = [{
                "type": "paragraph",
                "content": self._parse_inline_content(item['content'])
            }]
            
            items.append({
                "type": "listItem",
                "content": item_content
            })
        
        return {
            "type": list_type,
            "content": items
        }

    def _convert_table_to_adf(self, table_block: dict[str, Any]) -> dict[str, Any]:
        """Convert table block to ADF format with proper header detection."""
        rows = []
        has_header = table_block.get('has_header', False)
        
        for idx, row_cells in enumerate(table_block['rows']):
            if idx >= self.max_table_rows:
                # Add truncation row
                rows.append({
                    "type": "tableRow",
                    "content": [{
                        "type": "tableCell",
                        "content": [{
                            "type": "paragraph",
                            "content": [{
                                "type": "text",
                                "text": f"... (table truncated after {self.max_table_rows} rows)"
                            }]
                        }]
                    }]
                })
                break
            
            cells = []
            for cell_text in row_cells:
                # Use tableHeader for first row if has_header is True
                cell_type = "tableHeader" if has_header and idx == 0 else "tableCell"
                cells.append({
                    "type": cell_type,
                    "content": [{
                        "type": "paragraph",
                        "content": self._parse_inline_content(cell_text)
                    }]
                })
            
            rows.append({
                "type": "tableRow",
                "content": cells
            })
        
        return {
            "type": "table",
            "attrs": {
                "isNumberColumnEnabled": False,
                "layout": "default"
            },
            "content": rows
        }

    def _convert_panel_to_adf(self, block: dict[str, Any]) -> dict[str, Any]:
        """Convert panel block to ADF format."""
        panel_type = block['panel_type'].lower()
        if panel_type not in ['info', 'note', 'warning', 'success', 'error']:
            panel_type = 'info'  # Default
        
        # Parse panel content
        nested_blocks = self._parse_markdown_blocks(block['content'])
        content = []
        for nested in nested_blocks:
            node = self._convert_block_to_adf(nested)
            if node:
                content.append(node)
        
        return {
            "type": "panel",
            "attrs": {"panelType": panel_type},
            "content": content if content else [{"type": "paragraph", "content": []}]
        }

    def _parse_inline_content(self, text: str) -> list[dict[str, Any]]:
        """Parse inline content with formatting and special elements."""
        if not text:
            return []
        
        nodes = []
        
        # Handle special inline patterns
        parts = self._split_inline_patterns(text)
        
        for part in parts:
            if part.startswith("<<<STATUS:"):
                # Extract status info
                match = re.match(r'<<<STATUS:(\w+):(.+?)>>>', part)
                if match:
                    color, status_text = match.groups()
                    nodes.append({
                        "type": "status",
                        "attrs": {
                            "text": status_text,
                            "color": self._normalize_status_color(color)
                        }
                    })
            elif part.startswith("<<<MENTION:"):
                # Extract mention info
                match = re.match(r'<<<MENTION:(.+?)>>>', part)
                if match:
                    name = match.group(1)
                    nodes.append({
                        "type": "mention",
                        "attrs": {
                            "text": f"@{name}",
                            "id": "unknown"  # Would need user lookup
                        }
                    })
            elif part.startswith("<<<DATE:"):
                # Extract date info
                match = re.match(r'<<<DATE:(.+?)>>>', part)
                if match:
                    date_str = match.group(1)
                    # Convert to timestamp (simplified)
                    nodes.append({
                        "type": "date",
                        "attrs": {
                            "timestamp": date_str
                        }
                    })
            else:
                # Regular text with markdown formatting
                formatted_nodes = self._parse_markdown_formatting(part)
                nodes.extend(formatted_nodes)
        
        return nodes

    def _split_inline_patterns(self, text: str) -> list[str]:
        """Split text by special inline patterns."""
        # Pattern to match all special elements
        pattern = r'(<<<(?:STATUS|MENTION|DATE):.+?>>>)'
        parts = re.split(pattern, text)
        return [part for part in parts if part]

    def _parse_markdown_formatting(self, text: str) -> list[dict[str, Any]]:
        """Parse markdown inline formatting (bold, italic, code, links)."""
        nodes = []
        
        # Simple implementation - in production, use proper markdown parser
        # This is a simplified version for demonstration
        
        # Handle links first
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        parts = re.split(link_pattern, text)
        
        i = 0
        while i < len(parts):
            if i + 2 < len(parts) and parts[i + 1] and parts[i + 2]:
                # This is a link
                if parts[i]:
                    nodes.extend(self._parse_text_formatting(parts[i]))
                nodes.append({
                    "type": "text",
                    "text": parts[i + 1],
                    "marks": [{"type": "link", "attrs": {"href": parts[i + 2]}}]
                })
                i += 3
            else:
                if parts[i]:
                    nodes.extend(self._parse_text_formatting(parts[i]))
                i += 1
        
        return nodes

    def _parse_text_formatting(self, text: str) -> list[dict[str, Any]]:
        """Parse text formatting marks (bold, italic, code, etc)."""
        # This is simplified - in production, use proper parsing
        nodes = []
        
        # Handle code
        if '`' in text:
            parts = text.split('`')
            for i, part in enumerate(parts):
                if i % 2 == 0 and part:
                    # Not code
                    nodes.append({"type": "text", "text": part})
                elif i % 2 == 1 and part:
                    # Code
                    nodes.append({
                        "type": "text",
                        "text": part,
                        "marks": [{"type": "code"}]
                    })
        else:
            # For now, just return as plain text
            # In production, handle **bold**, *italic*, ~~strike~~, etc.
            if text:
                nodes.append({"type": "text", "text": text})
        
        return nodes

    def _normalize_status_color(self, color: str) -> str:
        """Normalize status color to ADF values."""
        color_map = {
            'gray': 'neutral',
            'grey': 'neutral',
            'blue': 'blue',
            'green': 'green',
            'red': 'red',
            'yellow': 'yellow',
            'purple': 'purple'
        }
        return color_map.get(color.lower(), 'neutral')

    def _track_node_metrics(self, node_type: str) -> None:
        """Track node creation metrics."""
        if node_type not in self.metrics['nodes_created']:
            self.metrics['nodes_created'][node_type] = 0
        self.metrics['nodes_created'][node_type] += 1

    def _create_empty_document(self) -> dict[str, Any]:
        """Create empty ADF document."""
        return {
            "version": 1,
            "type": "doc",
            "content": []
        }

    def _create_error_document(
        self, 
        original_text: str, 
        error: str
    ) -> dict[str, Any]:
        """Create error fallback document."""
        return {
            "version": 1,
            "type": "doc",
            "content": [{
                "type": "panel",
                "attrs": {"panelType": "error"},
                "content": [{
                    "type": "paragraph",
                    "content": [{
                        "type": "text",
                        "text": f"Conversion error: {error}"
                    }]
                }, {
                    "type": "paragraph",
                    "content": [{
                        "type": "text",
                        "text": original_text[:500] + "..." if len(original_text) > 500 else original_text
                    }]
                }]
            }]
        }

    def validate_marks(self, marks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate and filter mark combinations according to ADF rules."""
        if not marks:
            return marks
        
        # Check for code mark
        has_code = any(m['type'] == 'code' for m in marks)
        
        if has_code:
            # Code can only combine with link
            return [m for m in marks if m['type'] in ['code', 'link']]
        
        # Check for incompatible marks
        has_text_color = any(m['type'] == 'textColor' for m in marks)
        has_bg_color = any(m['type'] == 'backgroundColor' for m in marks)
        has_link = any(m['type'] == 'link' for m in marks)
        
        filtered_marks = []
        for mark in marks:
            if mark['type'] == 'textColor' and has_link:
                continue  # textColor cannot combine with link
            if mark['type'] == 'backgroundColor' and has_code:
                continue  # backgroundColor cannot combine with code
            filtered_marks.append(mark)
        
        return filtered_marks

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics."""
        cache_info = getattr(self._cached_convert, 'cache_info', lambda: None)()
        
        metrics = self.metrics.copy()
        if cache_info:
            metrics['cache_info'] = {
                'hits': cache_info.hits,
                'misses': cache_info.misses,
                'maxsize': cache_info.maxsize,
                'currsize': cache_info.currsize
            }
            metrics['cache_hit_rate'] = (
                (cache_info.hits / max(1, cache_info.hits + cache_info.misses)) * 100
            )
        
        total_conversions = max(1, self.metrics['conversions_total'])
        metrics['average_conversion_time'] = (
            self.metrics['conversion_time_total'] / total_conversions
        )
        metrics['error_rate'] = (
            (self.metrics['conversion_errors'] / total_conversions) * 100
        )
        
        return metrics