"""Examples demonstrating the ADF plugin architecture usage."""

from mcp_atlassian.formatting.adf_ast import ASTBasedADFGenerator
import json


def print_result(title: str, markdown: str, result: dict):
    """Pretty print conversion results."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Markdown:\n{markdown}")
    print(f"\nADF Output:")
    print(json.dumps(result, indent=2))


def main():
    """Run all plugin examples."""
    generator = ASTBasedADFGenerator()
    
    # Example 1: Panel Plugin
    panel_markdown = """:::panel type="warning"
This is a warning panel.

It supports **bold**, *italic*, and `code` formatting.
:::"""
    
    result = generator.markdown_to_adf(panel_markdown)
    print_result("Panel Plugin Example", panel_markdown, result)
    
    # Example 2: Multiple Panel Types
    multi_panel_markdown = """:::panel type="info"
Information panel
:::

:::panel type="error"
Error panel with **emphasis**
:::

:::panel type="success"
Success panel
:::"""
    
    result = generator.markdown_to_adf(multi_panel_markdown)
    print_result("Multiple Panel Types", multi_panel_markdown, result)
    
    # Example 3: Expand Plugin
    expand_markdown = """:::expand title="Implementation Details"
This section contains the technical implementation details.

- First detail
- Second detail
- Third detail with `code`
:::"""
    
    result = generator.markdown_to_adf(expand_markdown)
    print_result("Expand Plugin Example", expand_markdown, result)
    
    # Example 4: Media Plugin
    media_markdown = """:::media
type: image
id: att123456789
collection: contentId-987654321
width: 800
height: 600
layout: center
:::"""
    
    result = generator.markdown_to_adf(media_markdown)
    print_result("Media Plugin Example", media_markdown, result)
    
    # Example 5: Status Plugin
    status_markdown = """Project status update:
- Login feature: {status:color=green}Complete{/status}
- API integration: {status:color=yellow}In Progress{/status}
- Testing: {status:color=red}Blocked{/status}
- Documentation: {status:color=blue}Under Review{/status}"""
    
    result = generator.markdown_to_adf(status_markdown)
    print_result("Status Plugin Example", status_markdown, result)
    
    # Example 6: Date Plugin
    date_markdown = """Important dates:
- Project start: {date:2025-01-01}
- Milestone 1: {date:2025-02-15}
- Expected completion: {date:2025-06-30}"""
    
    result = generator.markdown_to_adf(date_markdown)
    print_result("Date Plugin Example", date_markdown, result)
    
    # Example 7: Mention Plugin
    mention_markdown = """Team members:
- Lead developer: @john.doe
- Designer: @jane.smith
- Project manager: @[Michael Johnson]
- QA engineer: @sarah_wilson"""
    
    result = generator.markdown_to_adf(mention_markdown)
    print_result("Mention Plugin Example", mention_markdown, result)
    
    # Example 8: Emoji Plugin
    emoji_markdown = """Reaction summary:
- Great work! :thumbsup:
- Made me smile :smile:
- Important :warning:
- Love it :heart:
- On fire :fire:"""
    
    result = generator.markdown_to_adf(emoji_markdown)
    print_result("Emoji Plugin Example", emoji_markdown, result)
    
    # Example 9: Layout Plugin
    layout_markdown = """:::layout columns=2
::: column
## Left Column
This is the content for the left column.
It can contain any markdown formatting.

- Bullet points
- **Bold text**
- *Italic text*
:::
::: column
## Right Column
This is the content for the right column.

1. Numbered lists
2. `Code snippets`
3. [Links](https://example.com)
:::
:::"""
    
    result = generator.markdown_to_adf(layout_markdown)
    print_result("Layout Plugin Example", layout_markdown, result)
    
    # Example 10: Combined Plugins
    combined_markdown = """:::panel type="info"
## Project Status for @john.doe

Last updated: {date:2025-01-30}

Overall status: {status:color=yellow}In Progress{/status} :fire:
:::

:::expand title="Detailed Timeline"
- Sprint 1: {status:color=green}Complete{/status} :check:
- Sprint 2: {status:color=yellow}In Progress{/status}
- Sprint 3: {status:color=grey}Not Started{/status}

Key milestone: {date:2025-02-15}
:::

:::layout columns=3
::: column
### Development
@jane.smith is leading development.
Status: {status:color=green}On Track{/status}
:::
::: column
### Testing
@[QA Team] is preparing test cases.
Status: {status:color=yellow}Preparing{/status}
:::
::: column
### Documentation
Need to assign someone :warning:
Status: {status:color=red}Not Started{/status}
:::
:::"""
    
    result = generator.markdown_to_adf(combined_markdown)
    print_result("Combined Plugins Example", combined_markdown, result)
    
    # Example 11: Nested Content
    nested_markdown = """:::panel type="note"
This panel contains various elements:

:::expand title="Nested Expand"
Even expands can be nested in panels!

Current status: {status:color=green}Working{/status}
:::

Contact @admin for more info :smile:
:::"""
    
    result = generator.markdown_to_adf(nested_markdown)
    print_result("Nested Content Example", nested_markdown, result)
    
    # Example 12: Empty Content Handling
    empty_markdown = """:::panel type="error"
:::

:::expand title="Empty Expand"
:::"""
    
    result = generator.markdown_to_adf(empty_markdown)
    print_result("Empty Content Handling", empty_markdown, result)


if __name__ == "__main__":
    main()