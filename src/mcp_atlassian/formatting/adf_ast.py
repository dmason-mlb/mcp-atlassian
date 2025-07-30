"""ADF AST-based generator using mistune for robust markdown parsing.

This module provides a robust markdown to ADF conversion using mistune's AST
parser, replacing the fragile custom line-by-line parser.
"""

import logging
from functools import lru_cache
from typing import Any, Optional, Union, List, Dict
import mistune

from .adf_validator import ADFValidator, get_validation_level
from .adf_plugins import registry as plugin_registry

logger = logging.getLogger(__name__)


def adf_extensions(md):
    """Mistune plugin to handle ADF extensions."""
    # Register layout blocks first with custom parser
    layout_pattern = r'^:::layout(?:\s|$)'
    md.block.register('layout_block',
                      layout_pattern,
                      parse_layout_block,
                      before='fenced_code')
    
    # Then register other ADF blocks
    # This pattern handles simple blocks like panel, expand that don't have nested :::
    # Updated to handle empty blocks (no content between ::: markers)
    pattern = r'^:::(panel|expand|media)(?:\s+([^\n]+))?\n([\s\S]*?)^:::$'
    md.block.register('adf_block', 
                      pattern, 
                      parse_adf_block, 
                      before='fenced_code')
    
    if md.renderer:
        if hasattr(md.renderer, 'render_layout_block'):
            md.renderer.register('layout_block', md.renderer.render_layout_block)
        if hasattr(md.renderer, 'render_adf_block'):
            md.renderer.register('adf_block', md.renderer.render_adf_block)


def parse_layout_block(self, m, state):
    """Parse layout blocks with proper nesting support."""
    text = state.src[m.start():]
    lines = text.split('\n')
    
    # Extract attributes from first line
    import re
    first_line = lines[0]
    attrs_match = re.match(r'^:::layout(?:\s+(.+))?$', first_line)
    attrs = attrs_match.group(1) if attrs_match else ''
    
    # Find the matching closing :::
    depth = 1
    end_line = 0
    
    for i, line in enumerate(lines[1:], 1):
        if line.strip().startswith(':::'):
            if line.strip() == ':::':
                depth -= 1
                if depth == 0:
                    end_line = i
                    break
            else:
                depth += 1
    
    if end_line == 0:
        # No matching closing found - treat as regular text
        return False
    
    # Extract the content
    content = '\n'.join(lines[1:end_line])
    full_match = '\n'.join(lines[:end_line + 1])
    
    token = {
        'type': 'layout_block',
        'raw': full_match,
        'block_type': 'layout',
        'attrs': attrs,
        'content': content
    }
    state.append_token(token)
    
    # Return new position
    return m.start() + len(full_match) + 1  # +1 for the newline


def parse_adf_block(self, m, state):
    """Parse ADF extension blocks."""
    # Extract directly from match groups
    block_type = m.group(1)  # e.g., "panel", "expand", "media"
    attrs = m.group(2) or ''  # e.g., 'type="info"'
    content = m.group(3) or ''  # Inner content
    
    # Create the token
    token = {
        'type': 'adf_block',
        'raw': m.group(0),
        'block_type': block_type,
        'attrs': attrs,
        'content': content
    }
    state.append_token(token)
    
    # Return the end position
    return m.end()


class ADFRenderer(mistune.BaseRenderer):
    """Mistune renderer that outputs ADF JSON instead of HTML."""
    
    NAME = 'adf'
    
    def __init__(self, validator: Optional[ADFValidator] = None,
                 max_table_rows: int = 50, max_list_items: int = 100,
                 inline_parser = None) -> None:
        """Initialize the ADF renderer.
        
        Args:
            validator: Optional ADF validator instance
            max_table_rows: Maximum rows before table truncation
            max_list_items: Maximum items before list truncation
            inline_parser: Inline parser instance for parsing content
        """
        super().__init__()
        self.validator = validator or ADFValidator(validation_level=get_validation_level())
        self.max_table_rows = max_table_rows
        self.max_list_items = max_list_items
        self._list_item_count = 0
        self._table_row_count = 0
        self.inline_parser = inline_parser
    
    def render_token(self, token: Dict[str, Any], state: mistune.core.BlockState) -> Any:
        """Render a single token to ADF node."""
        func_name = f"render_{token['type']}"
        func = getattr(self, func_name, None)
        if func:
            return func(token, state)
        else:
            # Fallback for unknown token types
            logger.warning(f"No renderer for token type: {token['type']}")
            return None
    
    def render_tokens(self, tokens: List[Dict[str, Any]], state: mistune.core.BlockState) -> List[Any]:
        """Render multiple tokens."""
        nodes = []
        for token in tokens:
            # Skip blank line tokens
            if token.get('type') == 'blank_line':
                continue
            node = self.render_token(token, state)
            if node:
                if isinstance(node, list):
                    nodes.extend(node)
                else:
                    nodes.append(node)
        
        # Filter out empty paragraphs (common after block plugins)
        filtered_nodes = []
        for node in nodes:
            if node.get('type') == 'paragraph':
                # Check if paragraph is empty or contains only empty text
                content = node.get('content', [])
                if content and len(content) == 1 and content[0].get('type') == 'text':
                    text = content[0].get('text', '')
                    if not text.strip():
                        continue  # Skip empty paragraph
            filtered_nodes.append(node)
        
        return filtered_nodes
    
    def __call__(self, tokens: List[Dict[str, Any]], state: mistune.core.BlockState) -> Dict[str, Any]:
        """Main render method called by mistune."""
        content = self.render_tokens(tokens, state)
        return {
            "version": 1,
            "type": "doc",
            "content": content
        }
    
    # Block-level renderers
    
    def render_paragraph(self, token: Dict[str, Any], state: mistune.core.BlockState) -> Dict[str, Any]:
        """Render a paragraph block."""
        content = self.render_inline_tokens(token.get('children', []), state)
        return {
            "type": "paragraph",
            "content": content
        }
    
    def render_heading(self, token: Dict[str, Any], state: mistune.core.BlockState) -> Dict[str, Any]:
        """Render a heading block."""
        content = self.render_inline_tokens(token.get('children', []), state)
        return {
            "type": "heading",
            "attrs": {"level": token['attrs']['level']},
            "content": content
        }
    
    def render_block_code(self, token: Dict[str, Any], state: mistune.core.BlockState) -> Dict[str, Any]:
        """Render a code block."""
        attrs = {}
        info = token.get('attrs', {}).get('info')
        if info:
            # Extract language from info string
            language = info.split()[0] if info else None
            if language:
                attrs["language"] = language
        
        return {
            "type": "codeBlock",
            "attrs": attrs,
            "content": [{"type": "text", "text": token['raw'].rstrip('\n')}]
        }
    
    def render_block_quote(self, token: Dict[str, Any], state: mistune.core.BlockState) -> Dict[str, Any]:
        """Render a blockquote."""
        # Recursively render nested content
        content = self.render_tokens(token.get('children', []), state)
        return {
            "type": "blockquote", 
            "content": content
        }
    
    def render_list(self, token: Dict[str, Any], state: mistune.core.BlockState) -> Dict[str, Any]:
        """Render a list (bullet or ordered)."""
        list_type = "orderedList" if token['attrs']['ordered'] else "bulletList"
        # Reset counter for new list
        self._list_item_count = 0
        
        # Render list items
        content = self.render_tokens(token.get('children', []), state)
        
        return {
            "type": list_type,
            "content": content
        }
    
    def render_list_item(self, token: Dict[str, Any], state: mistune.core.BlockState) -> Dict[str, Any]:
        """Render a list item."""
        self._list_item_count += 1
        
        # Check if we've hit the limit
        if self._list_item_count > self.max_list_items:
            return {
                "type": "listItem",
                "content": [{
                    "type": "paragraph",
                    "content": [{
                        "type": "text",
                        "text": f"... (list truncated after {self.max_list_items} items)"
                    }]
                }]
            }
        
        # Render child content
        content = self.render_tokens(token.get('children', []), state)
        
        return {
            "type": "listItem",
            "content": content
        }
    
    def render_thematic_break(self, token: Dict[str, Any], state: mistune.core.BlockState) -> Dict[str, Any]:
        """Render a horizontal rule."""
        return {"type": "rule"}
    
    def render_layout_block(self, token: Dict[str, Any], state: mistune.core.BlockState) -> Any:
        """Render layout blocks using the plugin system."""
        raw_text = token.get('raw', '')
        attrs = token.get('attrs', '')
        content = token.get('content', '')
        
        
        # Create render_content function
        def render_content(content, block_mode=False):
            """Helper to render content as markdown.
            
            Args:
                content: Markdown content to render
                block_mode: If True, parse as block-level markdown
            """
            if block_mode and content:
                # For block mode, we need to create a temporary parser
                # to avoid circular dependencies
                from mistune import create_markdown
                temp_parser = create_markdown(renderer=ADFRenderer(
                    validator=self.validator,
                    max_table_rows=self.max_table_rows,
                    max_list_items=self.max_list_items,
                    inline_parser=self.inline_parser
                ), plugins=[
                    'strikethrough', 'table', 'url', 'task_lists',
                    'def_list', 'abbr', 'mark', 'insert', 
                    'superscript', 'subscript', adf_extensions
                ])
                
                # Parse the content as a full document
                parsed = temp_parser(content)
                
                # Extract just the content part
                if isinstance(parsed, dict) and parsed.get('type') == 'doc':
                    return parsed.get('content', [])
                else:
                    return [parsed] if parsed else []
            elif self.inline_parser and content:
                # Create inline state with empty env and set src
                inline_state = mistune.core.InlineState({})
                inline_state.src = content
                tokens = self.inline_parser.parse(inline_state)
                result = self.render_inline_tokens(tokens, state)
                return result
            else:
                # Fallback - just return text
                return [{"type": "text", "text": content}]
        
        # Use the LayoutPlugin directly
        from .adf_plugins import LayoutPlugin
        plugin = LayoutPlugin()
        
        # Parse columns parameter
        import re
        num_columns = 2  # Default
        if attrs:
            cols_match = re.search(r'columns=(\d+)', attrs)
            if cols_match:
                num_columns = int(cols_match.group(1))
        
        # Parse individual columns
        column_pattern = re.compile(
            r'::: column\s*\n(.*?)\n:::',
            re.DOTALL
        )
        
        columns = []
        for col_match in column_pattern.finditer(content):
            columns.append(col_match.group(1).strip())
        
        # Create data structure for plugin
        data = {
            'type': 'layout',
            'num_columns': num_columns,
            'columns': columns
        }
        
        # Render using the plugin
        node = plugin.render_block(data, render_content)
        
        return node
    
    def render_adf_block(self, token: Dict[str, Any], state: mistune.core.BlockState) -> Any:
        """Render ADF extension blocks using the plugin system."""
        raw_text = token.get('raw', '')
        
        # First try to process with plugins
        def render_content(content, block_mode=False):
            """Helper to render content as markdown.
            
            Args:
                content: Markdown content to render
                block_mode: If True, parse as block-level markdown
            """
            if block_mode and content:
                # For block mode, we need to create a temporary parser
                # to avoid circular dependencies
                from mistune import create_markdown
                temp_parser = create_markdown(renderer=ADFRenderer(
                    validator=self.validator,
                    max_table_rows=self.max_table_rows,
                    max_list_items=self.max_list_items,
                    inline_parser=self.inline_parser
                ), plugins=[
                    'strikethrough', 'table', 'url', 'task_lists',
                    'def_list', 'abbr', 'mark', 'insert', 
                    'superscript', 'subscript', adf_extensions
                ])
                
                # Parse the content as a full document
                parsed = temp_parser(content)
                
                # Extract just the content part
                if isinstance(parsed, dict) and parsed.get('type') == 'doc':
                    return parsed.get('content', [])
                else:
                    return [parsed] if parsed else []
            elif self.inline_parser and content:
                # Create inline state with empty env and set src
                inline_state = mistune.core.InlineState({})
                inline_state.src = content
                tokens = self.inline_parser.parse(inline_state)
                result = self.render_inline_tokens(tokens, state)
                return result
            else:
                # Fallback - just return text
                return [{"type": "text", "text": content}]
        
        nodes = plugin_registry.process_block_text(raw_text, render_content)
        
        if nodes:
            return nodes[0]
        
        # If no plugin handled it, process the parsed content directly
        block_type = token.get('block_type', '')
        content = token.get('content', '')
        
        # Check if we have a panel block
        if block_type == 'panel':
            # Parse attributes (e.g., type="info")
            attrs = token.get('attrs', '')
            panel_type = 'info'  # default
            
            import re
            attr_match = re.search(r'type="(info|note|warning|success|error)"', attrs)
            if attr_match:
                panel_type = attr_match.group(1)
            
            # Parse the content as inline markdown
            content_nodes = []
            if content.strip():
                # Split into paragraphs and render each
                paragraphs = content.strip().split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        # Create inline state with empty env and set src
                        inline_state = mistune.core.InlineState({})
                        inline_state.src = para.strip()
                        inline_tokens = self.inline_parser.parse(inline_state) if self.inline_parser else []
                        inline_content = self.render_inline_tokens(inline_tokens, state)
                        if inline_content:
                            content_nodes.append({
                                "type": "paragraph",
                                "content": inline_content
                            })
            
            return {
                "type": "panel",
                "attrs": {"panelType": panel_type},
                "content": content_nodes or [{"type": "paragraph", "content": [{"type": "text", "text": ""}]}]
            }
        
        # Unknown block type - return as paragraph
        return {
            "type": "paragraph",
            "content": [{"type": "text", "text": raw_text}]
        }
    
    def render_block_text(self, token: Dict[str, Any], state: mistune.core.BlockState) -> Dict[str, Any]:
        """Render block text - typically wrapped in a paragraph."""
        # Block text usually contains inline content that should be in a paragraph
        content = self.render_inline_tokens(token.get('children', []), state)
        return {
            "type": "paragraph",
            "content": content
        }
    
    def render_table(self, token: Dict[str, Any], state: mistune.core.BlockState) -> Dict[str, Any]:
        """Render a table."""
        # Reset counter for new table
        self._table_row_count = 0
        
        # Process table head and body separately
        content = []
        for child in token.get('children', []):
            if child['type'] == 'table_head':
                content.extend(self.render_table_head(child, state))
            elif child['type'] == 'table_body':
                content.extend(self.render_table_body(child, state))
        
        return {
            "type": "table",
            "content": content
        }
    
    def render_table_head(self, token: Dict[str, Any], state: mistune.core.BlockState) -> List[Dict[str, Any]]:
        """Render table header rows."""
        # Table head contains cells directly, not rows
        self._table_row_count += 1
        
        if self._table_row_count > self.max_table_rows:
            return [self._create_truncation_row()]
        
        cells = []
        for cell_token in token.get('children', []):
            cells.append(self.render_table_cell(cell_token, state, is_head=True))
        
        return [{
            "type": "tableRow",
            "content": cells
        }]
    
    def render_table_body(self, token: Dict[str, Any], state: mistune.core.BlockState) -> List[Dict[str, Any]]:
        """Render table body rows."""
        rows = []
        for row_token in token.get('children', []):
            self._table_row_count += 1
            if self._table_row_count > self.max_table_rows:
                rows.append(self._create_truncation_row())
                break
            
            cells = []
            for cell_token in row_token.get('children', []):
                cells.append(self.render_table_cell(cell_token, state, is_head=False))
            
            rows.append({
                "type": "tableRow",
                "content": cells
            })
        return rows
    
    def render_table_cell(self, token: Dict[str, Any], state: mistune.core.BlockState, is_head: bool = False) -> Dict[str, Any]:
        """Render a table cell."""
        cell_type = "tableHeader" if is_head or token.get('attrs', {}).get('head') else "tableCell"
        
        # Render inline content
        inline_content = self.render_inline_tokens(token.get('children', []), state)
        
        return {
            "type": cell_type,
            "content": [{
                "type": "paragraph",
                "content": inline_content
            }]
        }
    
    def _create_truncation_row(self) -> Dict[str, Any]:
        """Create a truncation row for tables."""
        return {
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
        }
    
    # Inline-level renderers
    
    def render_inline_tokens(self, tokens: List[Dict[str, Any]], state: mistune.core.BlockState) -> List[Dict[str, Any]]:
        """Render inline tokens to ADF inline nodes."""
        nodes = []
        for token in tokens:
            node = self.render_inline_token(token, state)
            if node:
                if isinstance(node, list):
                    nodes.extend(node)
                else:
                    nodes.append(node)
        
        # Process the collected text for inline plugin matches
        nodes = self._process_inline_plugins(nodes)
        return nodes
    
    def render_inline_token(self, token: Dict[str, Any], state: mistune.core.BlockState) -> Any:
        """Render a single inline token."""
        token_type = token['type']
        
        if token_type == 'text':
            return {"type": "text", "text": token['raw']}
        elif token_type == 'emphasis':
            return self._apply_mark(token, {"type": "em"}, state)
        elif token_type == 'strong':
            return self._apply_mark(token, {"type": "strong"}, state)
        elif token_type == 'strikethrough':
            return self._apply_mark(token, {"type": "strike"}, state)
        elif token_type == 'codespan':
            # Mistune's codespan token already has the code text without backticks
            code_text = token.get('raw', '')
            return {
                "type": "text",
                "text": code_text,
                "marks": [{"type": "code"}]
            }
        elif token_type == 'link':
            mark = {"type": "link", "attrs": {"href": token['attrs']['url']}}
            if token['attrs'].get('title'):
                mark["attrs"]["title"] = token['attrs']['title']
            return self._apply_mark(token, mark, state)
        elif token_type == 'linebreak':
            return {"type": "hardBreak"}
        else:
            # Unknown inline type
            return {"type": "text", "text": token.get('raw', '')}
    
    def _apply_mark(self, token: Dict[str, Any], mark: Dict[str, Any], state: mistune.core.BlockState) -> Dict[str, Any]:
        """Apply a mark to inline content."""
        # Get the inner content
        children = token.get('children', [])
        if children:
            # Process children
            inner_nodes = self.render_inline_tokens(children, state)
            if len(inner_nodes) == 1 and inner_nodes[0].get('type') == 'text':
                # Single text node - apply mark directly
                node = inner_nodes[0]
                marks = node.get('marks', [])
                marks.append(mark)
                
                # Validate mark combinations
                is_valid, errors = self.validator.validate_marks(marks)
                if not is_valid:
                    if self.validator.validation_level == ADFValidator.VALIDATION_ERROR:
                        logger.error(f"Invalid mark combination: {'; '.join(errors)}")
                        # Filter marks to only valid combinations
                        # If code mark exists, only keep code and link marks
                        mark_types = {m['type'] for m in marks}
                        if 'code' in mark_types:
                            marks = [m for m in marks if m['type'] in ('code', 'link')]
                    elif self.validator.validation_level == ADFValidator.VALIDATION_WARN:
                        logger.warning(f"Invalid mark combination: {'; '.join(errors)}")
                
                node['marks'] = marks
                return node
            else:
                # Multiple nodes - need to handle differently
                # For now, just return the first text node with mark
                return {
                    "type": "text",
                    "text": self._extract_text(inner_nodes),
                    "marks": [mark]
                }
        else:
            # No children, use raw text
            return {
                "type": "text",
                "text": token.get('raw', ''),
                "marks": [mark]
            }
    
    def _extract_text(self, nodes: List[Dict[str, Any]]) -> str:
        """Extract text from nodes."""
        text_parts = []
        for node in nodes:
            if node.get('type') == 'text':
                text_parts.append(node.get('text', ''))
        return ''.join(text_parts)
    
    def _process_inline_plugins(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process inline nodes for plugin patterns."""
        import re
        
        # First, merge adjacent text nodes
        merged_nodes = []
        i = 0
        while i < len(nodes):
            if nodes[i].get('type') == 'text' and not nodes[i].get('marks'):
                # Start merging adjacent text nodes
                text_parts = [nodes[i]['text']]
                j = i + 1
                while j < len(nodes) and nodes[j].get('type') == 'text' and not nodes[j].get('marks'):
                    text_parts.append(nodes[j]['text'])
                    j += 1
                
                # Create merged node
                merged_nodes.append({
                    'type': 'text',
                    'text': ''.join(text_parts)
                })
                i = j
            else:
                # Non-text node or marked text, keep as-is
                merged_nodes.append(nodes[i])
                i += 1
        
        result = []
        
        for node in merged_nodes:
            if node.get('type') == 'text' and not node.get('marks'):
                # Only process plain text nodes
                text = node.get('text', '')
                
                # Collect all matches from all plugins
                all_matches = []
                for plugin in plugin_registry.get_inline_plugins():
                    if plugin.inline_pattern:
                        for match in plugin.inline_pattern.finditer(text):
                            all_matches.append((match, plugin))
                
                if all_matches:
                    # Sort matches by position
                    all_matches.sort(key=lambda x: x[0].start())
                    
                    # Split text and create nodes
                    last_end = 0
                    for match, plugin in all_matches:
                        # Add text before match
                        if match.start() > last_end:
                            result.append({
                                'type': 'text',
                                'text': text[last_end:match.start()]
                            })
                        
                        # Add plugin node
                        try:
                            data = plugin.parse_inline(match)
                            plugin_node = plugin.render_inline(data)
                            result.append(plugin_node)
                        except Exception as e:
                            logger.error(f"Error processing inline plugin {plugin.name}: {e}")
                            # Fall back to text
                            result.append({
                                'type': 'text',
                                'text': match.group(0)
                            })
                        
                        last_end = match.end()
                    
                    # Add remaining text
                    if last_end < len(text):
                        result.append({
                            'type': 'text',
                            'text': text[last_end:]
                        })
                else:
                    # No matches, keep original node
                    result.append(node)
            else:
                # Non-text node or marked text, keep as-is
                result.append(node)
        
        return result


class ASTBasedADFGenerator:
    """ADF generator using AST-based markdown parsing with mistune."""
    
    def __init__(self, max_table_rows: int = 50, max_list_items: int = 100) -> None:
        """Initialize the AST-based ADF generator.
        
        Args:
            max_table_rows: Maximum rows before table truncation
            max_list_items: Maximum items before list truncation
        """
        self.max_table_rows = max_table_rows
        self.max_list_items = max_list_items
        
        # Initialize validator
        self.validator = ADFValidator(validation_level=get_validation_level())
        
        # Create inline parser first
        self._inline_parser = mistune.InlineParser()
        
        # Create renderer with inline parser
        self.renderer = ADFRenderer(
            validator=self.validator,
            max_table_rows=max_table_rows,
            max_list_items=max_list_items,
            inline_parser=self._inline_parser
        )
        
        # Create mistune markdown parser with ADF renderer
        self.markdown = mistune.create_markdown(
            renderer=self.renderer,
            plugins=[
                'strikethrough',
                'table',
                'url',  # Auto-link URLs
                'task_lists',  # GitHub-style task lists
                'def_list',  # Definition lists
                'abbr',  # Abbreviations
                'mark',  # Marked/highlighted text
                'insert',  # Inserted text
                'superscript',  # Superscript
                'subscript',  # Subscript
                adf_extensions  # Our custom ADF extensions
            ]
        )
    
    @lru_cache(maxsize=256)
    def markdown_to_adf(self, markdown_text: str) -> Dict[str, Any]:
        """Convert markdown to ADF using AST parsing.
        
        Args:
            markdown_text: Input markdown text
            
        Returns:
            ADF document structure
        """
        try:
            if not markdown_text or not markdown_text.strip():
                return {
                    "version": 1,
                    "type": "doc",
                    "content": []
                }
            
            # Parse markdown to AST and render to ADF
            adf_doc = self.markdown(markdown_text)
            
            # Ensure we have a proper doc structure
            if not isinstance(adf_doc, dict) or adf_doc.get("type") != "doc":
                # Wrap in doc if needed
                adf_doc = {
                    "version": 1,
                    "type": "doc",
                    "content": [adf_doc] if adf_doc else []
                }
            
            # Validate if enabled
            is_valid, errors = self.validator.validate(adf_doc)
            if not is_valid and self.validator.validation_level == ADFValidator.VALIDATION_ERROR:
                logger.error(f"ADF validation failed: {'; '.join(errors)}")
                # Return error document
                return self._create_error_document(markdown_text, errors)
            
            return adf_doc
            
        except Exception as e:
            logger.error(f"AST-based ADF conversion failed: {e}", exc_info=True)
            return self._create_error_document(markdown_text, [str(e)])
    
    def _create_error_document(self, original_text: str, errors: List[str]) -> Dict[str, Any]:
        """Create an error document when conversion fails."""
        error_text = f"[ADF Conversion Error] {'; '.join(errors)}"
        if original_text:
            # Include truncated original text
            preview = original_text[:200] + "..." if len(original_text) > 200 else original_text
            error_text += f"\n\nOriginal text preview: {preview}"
        
        return {
            "version": 1,
            "type": "doc",
            "content": [{
                "type": "paragraph",
                "content": [{
                    "type": "text",
                    "text": error_text
                }]
            }]
        }