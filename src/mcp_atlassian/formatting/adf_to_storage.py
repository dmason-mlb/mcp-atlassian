"""Convert ADF (Atlassian Document Format) to Confluence storage format."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def adf_to_storage(adf_content: dict[str, Any]) -> str:
    """Convert ADF JSON to Confluence storage format (HTML).
    
    Args:
        adf_content: ADF document structure
        
    Returns:
        HTML string in Confluence storage format
    """
    if not isinstance(adf_content, dict):
        logger.warning("ADF content is not a dictionary, returning as string")
        return str(adf_content)
    
    if adf_content.get("type") != "doc":
        logger.warning("ADF content is not a document type")
        return str(adf_content)
    
    content_nodes = adf_content.get("content", [])
    if not content_nodes:
        return "<p></p>"
    
    html_parts = []
    for node in content_nodes:
        html_parts.append(_convert_node(node))
    
    return "".join(html_parts)


def _convert_node(node: dict[str, Any]) -> str:
    """Convert a single ADF node to HTML."""
    node_type = node.get("type", "")
    
    if node_type == "paragraph":
        return _convert_paragraph(node)
    elif node_type == "heading":
        return _convert_heading(node)
    elif node_type == "bulletList":
        return _convert_bullet_list(node)
    elif node_type == "orderedList":
        return _convert_ordered_list(node)
    elif node_type == "listItem":
        return _convert_list_item(node)
    elif node_type == "codeBlock":
        return _convert_code_block(node)
    elif node_type == "blockquote":
        return _convert_blockquote(node)
    elif node_type == "table":
        return _convert_table(node)
    elif node_type == "tableRow":
        return _convert_table_row(node)
    elif node_type == "tableCell" or node_type == "tableHeader":
        return _convert_table_cell(node, is_header=(node_type == "tableHeader"))
    elif node_type == "rule":
        return "<hr/>"
    else:
        logger.debug(f"Unknown node type: {node_type}")
        return _convert_paragraph(node)  # Fallback to paragraph


def _convert_paragraph(node: dict[str, Any]) -> str:
    """Convert paragraph node."""
    content = node.get("content", [])
    if not content:
        return "<p></p>"
    
    text_parts = []
    for text_node in content:
        text_parts.append(_convert_inline_node(text_node))
    
    text = "".join(text_parts)
    return f"<p>{text}</p>"


def _convert_heading(node: dict[str, Any]) -> str:
    """Convert heading node."""
    attrs = node.get("attrs", {})
    level = attrs.get("level", 1)
    
    content = node.get("content", [])
    text_parts = []
    for text_node in content:
        text_parts.append(_convert_inline_node(text_node))
    
    text = "".join(text_parts)
    return f"<h{level}>{text}</h{level}>"


def _convert_bullet_list(node: dict[str, Any]) -> str:
    """Convert bullet list node."""
    content = node.get("content", [])
    items = []
    for item_node in content:
        items.append(_convert_node(item_node))
    
    return f"<ul>{''.join(items)}</ul>"


def _convert_ordered_list(node: dict[str, Any]) -> str:
    """Convert ordered list node."""
    content = node.get("content", [])
    items = []
    for item_node in content:
        items.append(_convert_node(item_node))
    
    return f"<ol>{''.join(items)}</ol>"


def _convert_list_item(node: dict[str, Any]) -> str:
    """Convert list item node."""
    content = node.get("content", [])
    parts = []
    for child_node in content:
        parts.append(_convert_node(child_node))
    
    return f"<li>{''.join(parts)}</li>"


def _convert_code_block(node: dict[str, Any]) -> str:
    """Convert code block node."""
    attrs = node.get("attrs", {})
    language = attrs.get("language", "")
    
    content = node.get("content", [])
    text_parts = []
    for text_node in content:
        if text_node.get("type") == "text":
            text_parts.append(text_node.get("text", ""))
    
    code = "".join(text_parts)
    if language:
        return f'<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">{language}</ac:parameter><ac:plain-text-body><![CDATA[{code}]]></ac:plain-text-body></ac:structured-macro>'
    else:
        return f"<pre>{code}</pre>"


def _convert_blockquote(node: dict[str, Any]) -> str:
    """Convert blockquote node."""
    content = node.get("content", [])
    parts = []
    for child_node in content:
        parts.append(_convert_node(child_node))
    
    return f"<blockquote>{''.join(parts)}</blockquote>"


def _convert_table(node: dict[str, Any]) -> str:
    """Convert table node."""
    content = node.get("content", [])
    rows = []
    for row_node in content:
        rows.append(_convert_node(row_node))
    
    return f"<table>{''.join(rows)}</table>"


def _convert_table_row(node: dict[str, Any]) -> str:
    """Convert table row node."""
    content = node.get("content", [])
    cells = []
    for cell_node in content:
        cells.append(_convert_node(cell_node))
    
    return f"<tr>{''.join(cells)}</tr>"


def _convert_table_cell(node: dict[str, Any], is_header: bool = False) -> str:
    """Convert table cell node."""
    content = node.get("content", [])
    parts = []
    for child_node in content:
        parts.append(_convert_node(child_node))
    
    tag = "th" if is_header else "td"
    return f"<{tag}>{''.join(parts)}</{tag}>"


def _convert_inline_node(node: dict[str, Any]) -> str:
    """Convert inline text nodes."""
    node_type = node.get("type", "")
    
    if node_type == "text":
        text = node.get("text", "")
        marks = node.get("marks", [])
        
        # Apply marks (formatting)
        for mark in marks:
            mark_type = mark.get("type", "")
            if mark_type == "strong":
                text = f"<strong>{text}</strong>"
            elif mark_type == "em":
                text = f"<em>{text}</em>"
            elif mark_type == "code":
                text = f"<code>{text}</code>"
            elif mark_type == "strike":
                text = f"<s>{text}</s>"
            elif mark_type == "underline":
                text = f"<u>{text}</u>"
            elif mark_type == "link":
                href = mark.get("attrs", {}).get("href", "")
                text = f'<a href="{href}">{text}</a>'
        
        return text
    
    elif node_type == "hardBreak":
        return "<br/>"
    
    else:
        logger.debug(f"Unknown inline node type: {node_type}")
        return ""