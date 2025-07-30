"""Plugin architecture for ADF node extensions.

This module provides a plugin system for extending the ADF AST generator with
support for additional ADF nodes like panel, expand, status, etc.
"""

import re
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Pattern, Tuple

logger = logging.getLogger(__name__)


class BaseADFPlugin(ABC):
    """Base class for ADF node plugins."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the plugin."""
        pass
    
    @property
    @abstractmethod
    def block_pattern(self) -> Optional[Pattern[str]]:
        """Regex pattern for block-level node detection.
        
        Returns None for inline-only plugins.
        """
        pass
    
    @property
    @abstractmethod
    def inline_pattern(self) -> Optional[Pattern[str]]:
        """Regex pattern for inline node detection.
        
        Returns None for block-only plugins.
        """
        pass
    
    @abstractmethod
    def parse_block(self, match: re.Match[str], content: str) -> Dict[str, Any]:
        """Parse a block-level match into ADF node data.
        
        Args:
            match: The regex match object
            content: The content within the block
            
        Returns:
            Dictionary containing node data
        """
        pass
    
    @abstractmethod
    def parse_inline(self, match: re.Match[str]) -> Dict[str, Any]:
        """Parse an inline match into ADF node data.
        
        Args:
            match: The regex match object
            
        Returns:
            Dictionary containing node data
        """
        pass
    
    @abstractmethod
    def render_block(self, data: Dict[str, Any], render_content) -> Dict[str, Any]:
        """Render block data to ADF node.
        
        Args:
            data: Parsed node data
            render_content: Function to render nested content
            
        Returns:
            ADF node dictionary
        """
        pass
    
    @abstractmethod
    def render_inline(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Render inline data to ADF node.
        
        Args:
            data: Parsed node data
            
        Returns:
            ADF node dictionary
        """
        pass
    
    def validate(self, node: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate the rendered ADF node.
        
        Args:
            node: The ADF node to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        # Default implementation - subclasses can override
        return True, []


class PanelPlugin(BaseADFPlugin):
    """Plugin for ADF panel nodes.
    
    Supports syntax:
    :::panel type="info"
    Panel content here
    :::
    """
    
    @property
    def name(self) -> str:
        return "panel"
    
    @property
    def block_pattern(self) -> Optional[Pattern[str]]:
        # Match :::panel blocks with optional type attribute
        # Updated to handle empty panels (no content between markers)
        return re.compile(
            r'^:::panel(?:\s+type="(info|note|warning|success|error)")?\s*\n'
            r'(.*?)'
            r'^:::$',
            re.MULTILINE | re.DOTALL
        )
    
    @property
    def inline_pattern(self) -> Optional[Pattern[str]]:
        return None  # Panel is block-only
    
    def parse_block(self, match: re.Match[str], content: str) -> Dict[str, Any]:
        """Parse panel block match."""
        # The match groups are:
        # Group 1: panel type (info, note, warning, success, error) or None
        # Group 2: panel content
        panel_type = match.group(1) or 'info'  # Default to info
        panel_content = match.group(2) if match.group(2) else ''
        
        return {
            'type': 'panel',
            'panel_type': panel_type,
            'content': panel_content.strip()
        }
    
    def parse_inline(self, match: re.Match[str]) -> Dict[str, Any]:
        """Not applicable for panel blocks."""
        raise NotImplementedError("Panel is a block-only node")
    
    def render_block(self, data: Dict[str, Any], render_content) -> Dict[str, Any]:
        """Render panel data to ADF node."""
        # The render_content function passed in should handle block-level content
        # when called with block_mode=True
        content = data['content']
        
        if content.strip():
            # Ask render_content to parse as blocks, not inline
            wrapped_content = render_content(content, block_mode=True)
            
            # Ensure wrapped_content is a list
            if not isinstance(wrapped_content, list):
                wrapped_content = [wrapped_content]
        else:
            wrapped_content = [{"type": "paragraph", "content": [{"type": "text", "text": ""}]}]
        
        return {
            "type": "panel",
            "attrs": {
                "panelType": data['panel_type']
            },
            "content": wrapped_content
        }
    
    def render_inline(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Not applicable for panel blocks."""
        raise NotImplementedError("Panel is a block-only node")
    
    def validate(self, node: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate panel node against ADF spec."""
        errors = []
        
        # Check required fields
        if node.get('type') != 'panel':
            errors.append("Panel node must have type='panel'")
        
        attrs = node.get('attrs', {})
        panel_type = attrs.get('panelType')
        
        if not panel_type:
            errors.append("Panel must have panelType attribute")
        elif panel_type not in ('info', 'note', 'warning', 'success', 'error'):
            errors.append(f"Invalid panelType: {panel_type}")
        
        # Check content
        content = node.get('content', [])
        if not content:
            errors.append("Panel must have content")
        
        # Validate content types (only certain nodes allowed in panels)
        allowed_types = {'bulletList', 'heading', 'orderedList', 'paragraph'}
        for child in content:
            if child.get('type') not in allowed_types:
                errors.append(f"Panel cannot contain {child.get('type')} nodes")
        
        return len(errors) == 0, errors


class MediaPlugin(BaseADFPlugin):
    """Plugin for ADF media nodes (images, videos, files).
    
    Supports syntax:
    :::media
    type: image
    url: https://example.com/image.png
    alt: Description of image
    width: 800
    height: 600
    :::
    """
    
    @property
    def name(self) -> str:
        return "media"
    
    @property
    def block_pattern(self) -> Optional[Pattern[str]]:
        # Match :::media blocks
        return re.compile(
            r'^:::media\s*\n'
            r'((?:.*?\n)*?)'
            r'^:::$',
            re.MULTILINE | re.DOTALL
        )
    
    @property
    def inline_pattern(self) -> Optional[Pattern[str]]:
        return None  # Media is block-only
    
    def parse_block(self, match: re.Match[str], content: str) -> Dict[str, Any]:
        """Parse media block match."""
        media_content = match.group(1).strip()
        
        # Parse YAML-like content
        attrs = {}
        for line in media_content.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # Convert numeric values
                if key in ('width', 'height') and value.isdigit():
                    attrs[key] = int(value)
                else:
                    attrs[key] = value
        
        # Default to image type if not specified
        media_type = attrs.get('type', 'image')
        
        return {
            'type': 'media',
            'media_type': media_type,
            'attrs': attrs
        }
    
    def parse_inline(self, match: re.Match[str]) -> Dict[str, Any]:
        """Not applicable for media blocks."""
        raise NotImplementedError("Media is a block-only node")
    
    def render_block(self, data: Dict[str, Any], render_content) -> Dict[str, Any]:
        """Render media data to ADF node."""
        attrs = data['attrs']
        media_type = data['media_type']
        
        # Build media single node
        media_single = {
            "type": "mediaSingle",
            "content": [{
                "type": "media",
                "attrs": {
                    "id": attrs.get('id', ''),  # Media ID in Confluence
                    "type": media_type,
                    "collection": attrs.get('collection', '')
                }
            }]
        }
        
        # Add dimensions if provided
        if 'width' in attrs:
            media_single['content'][0]['attrs']['width'] = attrs['width']
        if 'height' in attrs:
            media_single['content'][0]['attrs']['height'] = attrs['height']
        
        # Add layout if specified
        if 'layout' in attrs:
            media_single['attrs'] = {"layout": attrs['layout']}
        
        return media_single
    
    def render_inline(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Not applicable for media blocks."""
        raise NotImplementedError("Media is a block-only node")
    
    def validate(self, node: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate media node against ADF spec."""
        errors = []
        
        # Check required fields
        if node.get('type') != 'mediaSingle':
            errors.append("Media node must have type='mediaSingle'")
        
        content = node.get('content', [])
        if not content:
            errors.append("MediaSingle must have content")
        elif len(content) != 1:
            errors.append("MediaSingle must have exactly one media child")
        elif content[0].get('type') != 'media':
            errors.append("MediaSingle child must be type='media'")
        
        # Check media attributes
        if content:
            media = content[0]
            media_attrs = media.get('attrs', {})
            
            if not media_attrs.get('id'):
                errors.append("Media must have an id attribute")
            
            media_type = media_attrs.get('type')
            if media_type not in ('file', 'image', 'video'):
                errors.append(f"Invalid media type: {media_type}")
        
        # Check layout attribute if present
        if 'attrs' in node:
            layout = node['attrs'].get('layout')
            if layout and layout not in ('center', 'wrap-left', 'wrap-right', 'wide', 'full-width'):
                errors.append(f"Invalid media layout: {layout}")
        
        return len(errors) == 0, errors


class ExpandPlugin(BaseADFPlugin):
    """Plugin for ADF expand (collapsible) nodes.
    
    Supports syntax:
    :::expand title="Click to expand"
    Content that is hidden by default.
    
    Can contain multiple paragraphs and formatting.
    :::
    """
    
    @property
    def name(self) -> str:
        return "expand"
    
    @property
    def block_pattern(self) -> Optional[Pattern[str]]:
        # Match :::expand blocks with optional title
        return re.compile(
            r'^:::expand(?:\s+title="([^"]+)")?\s*\n'
            r'(.*?)\n'
            r'^:::$',
            re.MULTILINE | re.DOTALL
        )
    
    @property
    def inline_pattern(self) -> Optional[Pattern[str]]:
        return None  # Expand is block-only
    
    def parse_block(self, match: re.Match[str], content: str) -> Dict[str, Any]:
        """Parse expand block match."""
        title = match.group(1) or 'Click to expand'
        expand_content = match.group(2).strip()
        
        return {
            'type': 'expand',
            'title': title,
            'content': expand_content
        }
    
    def parse_inline(self, match: re.Match[str]) -> Dict[str, Any]:
        """Not applicable for expand blocks."""
        raise NotImplementedError("Expand is a block-only node")
    
    def render_block(self, data: Dict[str, Any], render_content) -> Dict[str, Any]:
        """Render expand data to ADF node."""
        content = data['content']
        
        if content.strip():
            # Parse as block-level content
            wrapped_content = render_content(content, block_mode=True)
            
            # Ensure wrapped_content is a list
            if not isinstance(wrapped_content, list):
                wrapped_content = [wrapped_content]
        else:
            wrapped_content = [{"type": "paragraph", "content": [{"type": "text", "text": ""}]}]
        
        return {
            "type": "expand",
            "attrs": {
                "title": data['title']
            },
            "content": wrapped_content
        }
    
    def render_inline(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Not applicable for expand blocks."""
        raise NotImplementedError("Expand is a block-only node")
    
    def validate(self, node: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate expand node against ADF spec."""
        errors = []
        
        # Check required fields
        if node.get('type') != 'expand':
            errors.append("Expand node must have type='expand'")
        
        attrs = node.get('attrs', {})
        if not attrs.get('title'):
            errors.append("Expand must have title attribute")
        
        # Check content
        content = node.get('content', [])
        if not content:
            errors.append("Expand must have content")
        
        # Validate content types (only certain nodes allowed in expand)
        allowed_types = {'bulletList', 'heading', 'orderedList', 'paragraph', 'panel', 'blockquote', 'codeBlock'}
        for child in content:
            if child.get('type') not in allowed_types:
                errors.append(f"Expand cannot contain {child.get('type')} nodes")
        
        return len(errors) == 0, errors


class StatusPlugin(BaseADFPlugin):
    """Plugin for ADF status inline nodes.
    
    Supports syntax:
    {status:color=green}Done{/status}
    {status:color=yellow}In Progress{/status}
    {status:color=red}Blocked{/status}
    """
    
    @property
    def name(self) -> str:
        return "status"
    
    @property
    def block_pattern(self) -> Optional[Pattern[str]]:
        return None  # Status is inline-only
    
    @property
    def inline_pattern(self) -> Optional[Pattern[str]]:
        # Match {status:color=X}text{/status}
        return re.compile(
            r'\{status:color=(green|yellow|red|blue|purple|grey)\}'
            r'([^{]+?)'
            r'\{/status\}'
        )
    
    def parse_block(self, match: re.Match[str], content: str) -> Dict[str, Any]:
        """Not applicable for status inline nodes."""
        raise NotImplementedError("Status is an inline-only node")
    
    def parse_inline(self, match: re.Match[str]) -> Dict[str, Any]:
        """Parse status inline match."""
        color = match.group(1)
        text = match.group(2)
        
        return {
            'type': 'status',
            'color': color,
            'text': text
        }
    
    def render_block(self, data: Dict[str, Any], render_content) -> Dict[str, Any]:
        """Not applicable for status inline nodes."""
        raise NotImplementedError("Status is an inline-only node")
    
    def render_inline(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Render status data to ADF node."""
        return {
            "type": "status",
            "attrs": {
                "text": data['text'],
                "color": data['color']
            }
        }
    
    def validate(self, node: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate status node against ADF spec."""
        errors = []
        
        if node.get('type') != 'status':
            errors.append("Status node must have type='status'")
        
        attrs = node.get('attrs', {})
        if not attrs.get('text'):
            errors.append("Status must have text attribute")
        
        color = attrs.get('color')
        if color not in ('green', 'yellow', 'red', 'blue', 'purple', 'grey'):
            errors.append(f"Invalid status color: {color}")
        
        return len(errors) == 0, errors


class DatePlugin(BaseADFPlugin):
    """Plugin for ADF date inline nodes.
    
    Supports syntax:
    {date:2024-03-15}
    """
    
    @property
    def name(self) -> str:
        return "date"
    
    @property
    def block_pattern(self) -> Optional[Pattern[str]]:
        return None  # Date is inline-only
    
    @property
    def inline_pattern(self) -> Optional[Pattern[str]]:
        # Match {date:YYYY-MM-DD}
        return re.compile(r'\{date:(\d{4}-\d{2}-\d{2})\}')
    
    def parse_block(self, match: re.Match[str], content: str) -> Dict[str, Any]:
        """Not applicable for date inline nodes."""
        raise NotImplementedError("Date is an inline-only node")
    
    def parse_inline(self, match: re.Match[str]) -> Dict[str, Any]:
        """Parse date inline match."""
        date_str = match.group(1)
        
        # Convert to timestamp (milliseconds since epoch)
        try:
            from datetime import datetime
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            timestamp = int(dt.timestamp() * 1000)
        except ValueError:
            # Invalid date, use current timestamp
            from datetime import datetime
            timestamp = int(datetime.now().timestamp() * 1000)
        
        return {
            'type': 'date',
            'timestamp': timestamp
        }
    
    def render_block(self, data: Dict[str, Any], render_content) -> Dict[str, Any]:
        """Not applicable for date inline nodes."""
        raise NotImplementedError("Date is an inline-only node")
    
    def render_inline(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Render date data to ADF node."""
        return {
            "type": "date",
            "attrs": {
                "timestamp": data['timestamp']
            }
        }
    
    def validate(self, node: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate date node against ADF spec."""
        errors = []
        
        if node.get('type') != 'date':
            errors.append("Date node must have type='date'")
        
        attrs = node.get('attrs', {})
        if 'timestamp' not in attrs:
            errors.append("Date must have timestamp attribute")
        elif not isinstance(attrs['timestamp'], (int, float)):
            errors.append("Date timestamp must be a number")
        
        return len(errors) == 0, errors


class MentionPlugin(BaseADFPlugin):
    """Plugin for ADF mention inline nodes.
    
    Supports syntax:
    @username
    @[John Doe]
    """
    
    @property
    def name(self) -> str:
        return "mention"
    
    @property
    def block_pattern(self) -> Optional[Pattern[str]]:
        return None  # Mention is inline-only
    
    @property
    def inline_pattern(self) -> Optional[Pattern[str]]:
        # Match @username or @[Full Name]
        # Allow dots in usernames
        return re.compile(r'@(?:([a-zA-Z0-9_.-]+)|\[([^\]]+)\])')
    
    def parse_block(self, match: re.Match[str], content: str) -> Dict[str, Any]:
        """Not applicable for mention inline nodes."""
        raise NotImplementedError("Mention is an inline-only node")
    
    def parse_inline(self, match: re.Match[str]) -> Dict[str, Any]:
        """Parse mention inline match."""
        # Either simple username or bracketed full name
        username = match.group(1)
        full_name = match.group(2)
        
        text = username or full_name
        
        return {
            'type': 'mention',
            'text': text,
            'id': text.lower().replace(' ', '.')  # Simple ID generation
        }
    
    def render_block(self, data: Dict[str, Any], render_content) -> Dict[str, Any]:
        """Not applicable for mention inline nodes."""
        raise NotImplementedError("Mention is an inline-only node")
    
    def render_inline(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Render mention data to ADF node."""
        return {
            "type": "mention",
            "attrs": {
                "id": data['id'],
                "text": f"@{data['text']}"
            }
        }
    
    def validate(self, node: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate mention node against ADF spec."""
        errors = []
        
        if node.get('type') != 'mention':
            errors.append("Mention node must have type='mention'")
        
        attrs = node.get('attrs', {})
        if not attrs.get('id'):
            errors.append("Mention must have id attribute")
        
        return len(errors) == 0, errors


class EmojiPlugin(BaseADFPlugin):
    """Plugin for ADF emoji inline nodes.
    
    Supports syntax:
    :smile:
    :thumbsup:
    :warning:
    """
    
    # Common emoji mappings
    EMOJI_MAP = {
        'smile': '😊',
        'thumbsup': '👍',
        'thumbsdown': '👎',
        'warning': '⚠️',
        'info': 'ℹ️',
        'check': '✅',
        'cross': '❌',
        'star': '⭐',
        'heart': '❤️',
        'fire': '🔥'
    }
    
    @property
    def name(self) -> str:
        return "emoji"
    
    @property
    def block_pattern(self) -> Optional[Pattern[str]]:
        return None  # Emoji is inline-only
    
    @property
    def inline_pattern(self) -> Optional[Pattern[str]]:
        # Match :emoji_name:
        return re.compile(r':([a-zA-Z0-9_]+):')
    
    def parse_block(self, match: re.Match[str], content: str) -> Dict[str, Any]:
        """Not applicable for emoji inline nodes."""
        raise NotImplementedError("Emoji is an inline-only node")
    
    def parse_inline(self, match: re.Match[str]) -> Dict[str, Any]:
        """Parse emoji inline match."""
        shortname = match.group(1)
        
        return {
            'type': 'emoji',
            'shortname': shortname,
            'text': self.EMOJI_MAP.get(shortname, f':{shortname}:')
        }
    
    def render_block(self, data: Dict[str, Any], render_content) -> Dict[str, Any]:
        """Not applicable for emoji inline nodes."""
        raise NotImplementedError("Emoji is an inline-only node")
    
    def render_inline(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Render emoji data to ADF node."""
        return {
            "type": "emoji",
            "attrs": {
                "shortName": f":{data['shortname']}:",
                "text": data['text']
            }
        }
    
    def validate(self, node: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate emoji node against ADF spec."""
        errors = []
        
        if node.get('type') != 'emoji':
            errors.append("Emoji node must have type='emoji'")
        
        attrs = node.get('attrs', {})
        if not attrs.get('shortName'):
            errors.append("Emoji must have shortName attribute")
        
        return len(errors) == 0, errors


class LayoutPlugin(BaseADFPlugin):
    """Plugin for ADF layout nodes (multi-column layouts).
    
    Supports syntax:
    :::layout columns=2
    ::: column
    Content for first column.
    :::
    ::: column
    Content for second column.
    :::
    :::
    """
    
    @property
    def name(self) -> str:
        return "layout"
    
    @property
    def block_pattern(self) -> Optional[Pattern[str]]:
        # Match the entire :::layout block including nested columns
        # This needs to be greedy and capture everything until the final :::
        return re.compile(
            r'^(:::layout(?:\s+columns=\d+)?.*?^:::)$',
            re.MULTILINE | re.DOTALL
        )
    
    @property
    def inline_pattern(self) -> Optional[Pattern[str]]:
        return None  # Layout is block-only
    
    def parse_block(self, match: re.Match[str], content: str) -> Dict[str, Any]:
        """Parse layout block match."""
        # For layout blocks, the match gives us the full block
        full_block = match.group(0)
        
        # Parse attributes from the first line
        lines = full_block.split('\n')
        first_line = lines[0]
        
        # Extract columns parameter
        import re as re_module
        cols_match = re_module.search(r'columns=(\d+)', first_line)
        num_columns = int(cols_match.group(1)) if cols_match else 2
        
        # Find content between :::layout and closing :::
        content_start = full_block.find('\n') + 1
        content_end = full_block.rfind('\n:::')
        inner_content = full_block[content_start:content_end] if content_end > content_start else ''
        
        # Parse individual columns with a simpler pattern
        # Match ::: column through to the next ::: (either column or end)
        column_pattern = re_module.compile(
            r'::: column\s*\n(.*?)\n:::',
            re_module.DOTALL
        )
        
        columns = []
        for col_match in column_pattern.finditer(inner_content):
            columns.append(col_match.group(1).strip())
        
        return {
            'type': 'layout',
            'num_columns': num_columns,
            'columns': columns
        }
    
    def parse_inline(self, match: re.Match[str]) -> Dict[str, Any]:
        """Not applicable for layout blocks."""
        raise NotImplementedError("Layout is a block-only node")
    
    def render_block(self, data: Dict[str, Any], render_content) -> Dict[str, Any]:
        """Render layout data to ADF node."""
        columns = []
        
        for column_content in data['columns']:
            # Parse column content as block-level markdown
            if column_content.strip():
                section_content = render_content(column_content, block_mode=True)
                
                # Ensure section_content is a list
                if not isinstance(section_content, list):
                    section_content = [section_content]
            else:
                section_content = [{
                    "type": "paragraph",
                    "content": [{
                        "type": "text",
                        "text": ""
                    }]
                }]
            
            # Create a layoutColumn with layoutSection
            columns.append({
                "type": "layoutColumn",
                "attrs": {
                    "width": 100.0 / data['num_columns']  # Equal width columns
                },
                "content": [{
                    "type": "layoutSection",
                    "content": section_content
                }]
            })
        
        # Ensure we have the expected number of columns
        while len(columns) < data['num_columns']:
            columns.append({
                "type": "layoutColumn",
                "attrs": {
                    "width": 100.0 / data['num_columns']
                },
                "content": [{
                    "type": "layoutSection",
                    "content": [{
                        "type": "paragraph",
                        "content": [{
                            "type": "text",
                            "text": ""
                        }]
                    }]
                }]
            })
        
        # Return the layout node with columns
        return {
            "type": "layout",
            "content": columns
        }
    
    def render_inline(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Not applicable for layout blocks."""
        raise NotImplementedError("Layout is a block-only node")
    
    def validate(self, node: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate layout node against ADF spec."""
        errors = []
        
        # Check required fields
        if node.get('type') != 'layout':
            errors.append("Layout node must have type='layout'")
        
        # Check columns
        content = node.get('content', [])
        if not content:
            errors.append("Layout must have content columns")
        
        for column in content:
            if column.get('type') != 'layoutColumn':
                errors.append(f"Layout can only contain layoutColumn nodes, not {column.get('type')}")
            
            # Check column attributes
            attrs = column.get('attrs', {})
            if 'width' not in attrs:
                errors.append("LayoutColumn must have width attribute")
            elif not isinstance(attrs['width'], (int, float)):
                errors.append("LayoutColumn width must be a number")
            elif attrs['width'] < 0 or attrs['width'] > 100:
                errors.append("LayoutColumn width must be between 0 and 100")
            
            # Check sections
            column_content = column.get('content', [])
            if not column_content:
                errors.append("LayoutColumn must have content sections")
            
            for section in column_content:
                if section.get('type') != 'layoutSection':
                    errors.append(f"LayoutColumn can only contain layoutSection nodes, not {section.get('type')}")
        
        return len(errors) == 0, errors


class PluginRegistry:
    """Registry for managing ADF plugins."""
    
    def __init__(self):
        self.plugins: Dict[str, BaseADFPlugin] = {}
        self._block_plugins: List[BaseADFPlugin] = []
        self._inline_plugins: List[BaseADFPlugin] = []
    
    def register(self, plugin: BaseADFPlugin) -> None:
        """Register a plugin.
        
        Args:
            plugin: The plugin to register
        """
        if plugin.name in self.plugins:
            logger.warning(f"Overriding existing plugin: {plugin.name}")
        
        self.plugins[plugin.name] = plugin
        
        # Categorize by type
        if plugin.block_pattern:
            self._block_plugins.append(plugin)
        if plugin.inline_pattern:
            self._inline_plugins.append(plugin)
        
        logger.debug(f"Registered plugin: {plugin.name}")
    
    def unregister(self, name: str) -> None:
        """Unregister a plugin by name.
        
        Args:
            name: The plugin name
        """
        if name in self.plugins:
            plugin = self.plugins[name]
            del self.plugins[name]
            
            # Remove from categorized lists
            if plugin in self._block_plugins:
                self._block_plugins.remove(plugin)
            if plugin in self._inline_plugins:
                self._inline_plugins.remove(plugin)
            
            logger.debug(f"Unregistered plugin: {name}")
    
    def get_block_plugins(self) -> List[BaseADFPlugin]:
        """Get all plugins that handle block nodes."""
        return self._block_plugins.copy()
    
    def get_inline_plugins(self) -> List[BaseADFPlugin]:
        """Get all plugins that handle inline nodes."""
        return self._inline_plugins.copy()
    
    def process_block_text(self, text: str, render_content) -> List[Dict[str, Any]]:
        """Process text for block-level plugin matches.
        
        Args:
            text: The markdown text to process
            render_content: Function to render nested content
            
        Returns:
            List of ADF nodes found by plugins
        """
        nodes = []
        
        for plugin in self._block_plugins:
            pattern = plugin.block_pattern
            if not pattern:
                continue
            
            for match in pattern.finditer(text):
                try:
                    data = plugin.parse_block(match, text)
                    node = plugin.render_block(data, render_content)
                    
                    # Validate if enabled
                    is_valid, errors = plugin.validate(node)
                    if not is_valid:
                        logger.warning(f"Plugin {plugin.name} validation errors: {errors}")
                    
                    nodes.append(node)
                except Exception as e:
                    logger.error(f"Error in plugin {plugin.name}: {e}", exc_info=True)
        
        return nodes
    
    def process_inline_text(self, text: str) -> List[Dict[str, Any]]:
        """Process text for inline plugin matches.
        
        Args:
            text: The text to process
            
        Returns:
            List of inline ADF nodes found by plugins
        """
        nodes = []
        
        for plugin in self._inline_plugins:
            pattern = plugin.inline_pattern
            if not pattern:
                continue
            
            for match in pattern.finditer(text):
                try:
                    data = plugin.parse_inline(match)
                    node = plugin.render_inline(data)
                    
                    # Validate if enabled
                    is_valid, errors = plugin.validate(node)
                    if not is_valid:
                        logger.warning(f"Plugin {plugin.name} validation errors: {errors}")
                    
                    nodes.append(node)
                except Exception as e:
                    logger.error(f"Error in plugin {plugin.name}: {e}")
        
        return nodes


# Global registry instance
registry = PluginRegistry()

# Register default plugins
registry.register(PanelPlugin())
registry.register(MediaPlugin())
registry.register(ExpandPlugin())
registry.register(StatusPlugin())
registry.register(DatePlugin())
registry.register(MentionPlugin())
registry.register(EmojiPlugin())
registry.register(LayoutPlugin())