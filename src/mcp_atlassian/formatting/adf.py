"""ADF (Atlassian Document Format) generator for converting markdown to ADF JSON.

This module provides functionality to convert markdown text to ADF format that is 
required by Jira and Confluence Cloud APIs. It uses a visitor pattern to transform 
markdown AST nodes into proper ADF JSON structure.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Union

import markdown
from markdown.extensions import codehilite, tables
from markdown.treeprocessors import Treeprocessor

logger = logging.getLogger(__name__)


class ADFGenerator:
    """Generator for converting markdown text to Atlassian Document Format (ADF) JSON."""

    def __init__(self) -> None:
        """Initialize the ADF generator with markdown parser."""
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
        
    def markdown_to_adf(self, markdown_text: str) -> Dict[str, Any]:
        """
        Convert markdown text to ADF JSON format.
        
        Args:
            markdown_text: Input markdown text to convert
            
        Returns:
            Dictionary representing ADF JSON structure
            
        Raises:
            ValueError: If markdown conversion fails
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
            
    def _create_empty_document(self) -> Dict[str, Any]:
        """Create an empty ADF document."""
        return {
            "version": 1,
            "type": "doc", 
            "content": []
        }
        
    def _create_plain_text_document(self, text: str) -> Dict[str, Any]:
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
        
    def _html_to_adf_content(self, html: str) -> List[Dict[str, Any]]:
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
            
    def _convert_html_element_to_adf(self, element) -> Optional[Dict[str, Any]]:
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
        
    def _convert_heading(self, element) -> Dict[str, Any]:
        """Convert heading element to ADF heading."""
        level = int(element.name[1])  # Extract number from h1, h2, etc.
        
        return {
            "type": "heading",
            "attrs": {"level": level},
            "content": self._convert_inline_content(element)
        }
        
    def _convert_paragraph(self, element) -> Dict[str, Any]:
        """Convert paragraph element to ADF paragraph."""
        content = self._convert_inline_content(element)
        
        # Don't create empty paragraphs
        if not content:
            return self._create_empty_paragraph()
            
        return {
            "type": "paragraph",
            "content": content
        }
        
    def _convert_list(self, element) -> Dict[str, Any]:
        """Convert list element to ADF bulletList or orderedList."""
        list_type = "orderedList" if element.name == "ol" else "bulletList"
        
        content = []
        for li in element.find_all('li', recursive=False):
            list_item_content = self._convert_list_item_content(li)
            if list_item_content:
                content.append({
                    "type": "listItem",
                    "content": list_item_content
                })
                
        return {
            "type": list_type,
            "content": content
        }
        
    def _convert_list_item_content(self, li_element) -> List[Dict[str, Any]]:
        """Convert list item content to ADF format."""
        content = []
        
        # Handle nested elements in list item
        for child in li_element.children:
            if hasattr(child, 'name'):
                if child.name in ['ul', 'ol']:
                    # Nested list
                    content.append(self._convert_list(child))
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
                        content.append({
                            "type": "paragraph", 
                            "content": [{"type": "text", "text": text}]
                        })
            elif child.strip():
                # Direct text content
                content.append({
                    "type": "paragraph",
                    "content": [{"type": "text", "text": child.strip()}]
                })
                
        # If no content found, create empty paragraph
        return content if content else [self._create_empty_paragraph()]
        
    def _convert_code_block(self, element) -> Dict[str, Any]:
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
            
    def _convert_blockquote(self, element) -> Dict[str, Any]:
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
        
    def _convert_table(self, element) -> Dict[str, Any]:
        """Convert table to ADF table (basic implementation)."""
        # This is a simplified table conversion
        # Full table support would require more complex logic
        
        rows = []
        for tr in element.find_all('tr'):
            cells = []
            for td in tr.find_all(['td', 'th']):
                cell_content = self._convert_inline_content(td)
                cells.append({
                    "type": "tableCell",
                    "content": [{
                        "type": "paragraph",
                        "content": cell_content if cell_content else [{"type": "text", "text": ""}]
                    }]
                })
            if cells:
                rows.append({
                    "type": "tableRow",
                    "content": cells
                })
                
        return {
            "type": "table",
            "content": rows
        }
        
    def _convert_rule(self) -> Dict[str, Any]:
        """Convert horizontal rule to ADF rule."""
        return {"type": "rule"}
        
    def _convert_inline_content(self, element) -> List[Dict[str, Any]]:
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
        
    def _convert_inline_element(self, element) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """Convert inline HTML element to ADF inline node."""
        if not hasattr(element, 'name') or element.name is None:
            return None
        tag_name = element.name.lower()
        text_content = element.get_text()
        
        if not text_content.strip():
            return None
            
        # Basic text formatting
        marks = []
        
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
                    nested_content.append({
                        "type": "text",
                        "text": child.strip(),
                        "marks": marks if marks else None
                    })
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
            
    def _create_empty_paragraph(self) -> Dict[str, Any]:
        """Create an empty ADF paragraph."""
        return {
            "type": "paragraph",
            "content": []
        }
        
    def _create_plain_text_paragraph(self, text: str) -> Dict[str, Any]:
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
        
    def validate_adf(self, adf_json: Dict[str, Any]) -> bool:
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
                return False
                
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