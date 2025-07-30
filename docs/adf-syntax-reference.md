# ADF Syntax Quick Reference

## Standard Markdown Elements

### Text Formatting

| Syntax | Example | Result |
|--------|---------|--------|
| Bold | `**text**` or `__text__` | **text** |
| Italic | `*text*` or `_text_` | *text* |
| Strikethrough | `~~text~~` | ~~text~~ |
| Code | `` `code` `` | `code` |
| Bold + Italic | `***text***` | ***text*** |

### Headings

```markdown
# Heading 1
## Heading 2
### Heading 3
#### Heading 4
##### Heading 5
###### Heading 6
```

### Lists

#### Unordered Lists
```markdown
- Item 1
- Item 2
  - Nested item (2 spaces)
    - Deep nested (4 spaces)
```

#### Ordered Lists
```markdown
1. First item
2. Second item
   1. Nested item
   2. Another nested
```

#### Task Lists
```markdown
- [ ] Unchecked task
- [x] Checked task
```

### Links and Images

```markdown
[Link text](https://example.com)
[Link with title](https://example.com "Title")
[Reference link][ref]

[ref]: https://example.com

![Alt text](image.jpg)
```

### Code Blocks

````markdown
```python
def hello():
    print("Hello, world!")
```
````

### Tables

```markdown
| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |
```

### Blockquotes

```markdown
> This is a quote
> 
> > Nested quote
```

### Horizontal Rule

```markdown
---
***
___
```

## Extended Markdown (Mistune Plugins)

### Marked Text (Highlight)

```markdown
==highlighted text==
```

### Superscript and Subscript

```markdown
x^2^ + y^2^ = z^2^
H~2~O
```

### Inserted Text

```markdown
++inserted text++
```

### Definition Lists

```markdown
Term 1
: Definition 1

Term 2
: Definition 2a
: Definition 2b
```

### Abbreviations

```markdown
The HTML specification
*[HTML]: HyperText Markup Language
```

## ADF-Specific Elements (Plugin Syntax)

### Panel Blocks

```markdown
:::panel type="info"
This is an informational panel.
:::

:::panel type="note"
Note panel content.
:::

:::panel type="warning"
Warning message here.
:::

:::panel type="success"
Success notification.
:::

:::panel type="error"
Error message.
:::
```

### Expand/Collapse Blocks

```markdown
:::expand title="Click to expand"
Hidden content goes here.

Can include multiple paragraphs.
:::

:::expand title="Details"
- List items work
- Inside expand blocks
:::
```

### Media Blocks

```markdown
:::media
type: image
id: confluence-attachment-id
collection: contentId-123456
width: 800
height: 600
layout: center
:::
```

Layout options: `center`, `wrap-left`, `wrap-right`, `wide`, `full-width`

### Layout (Multi-Column)

```markdown
:::layout columns=2
::: column
First column content.

Can include any markdown.
:::
::: column
Second column content.

Also supports all markdown.
:::
:::
```

Three columns:
```markdown
:::layout columns=3
::: column
Column 1
:::
::: column
Column 2
:::
::: column
Column 3
:::
:::
```

### Status Badges (Inline)

```markdown
Status: {status:color=green}Complete{/status}
Status: {status:color=yellow}In Progress{/status}
Status: {status:color=red}Blocked{/status}
Status: {status:color=blue}Information{/status}
Status: {status:color=purple}Research{/status}
Status: {status:color=grey}Cancelled{/status}
```

### Date Elements (Inline)

```markdown
Due date: {date:2025-03-15}
Created: {date:2025-01-30}
```

### User Mentions (Inline)

```markdown
Simple mention: @username
Mention with dots: @john.doe
Full name mention: @[John Doe]
Email mention: @[user@example.com]
```

### Emoji (Inline)

```markdown
Common emojis:
:smile: :thumbsup: :thumbsdown:
:warning: :info: :check:
:cross: :star: :heart: :fire:
```

## Combining Elements

### Panel with Rich Content

```markdown
:::panel type="info"
# Panel Heading

This panel contains **bold**, *italic*, and `code`.

- List item 1
- List item 2

| Table | In Panel |
|-------|----------|
| Yes   | It works |

> Even quotes work
:::
```

### Expand with Code

```markdown
:::expand title="Code Example"
Here's how to use this feature:

```javascript
function example() {
    return "Hello!";
}
```

**Note**: All formatting works inside expand blocks.
:::
```

### Layout with Plugins

```markdown
:::layout columns=2
::: column
:::panel type="info"
Left panel
:::
:::
::: column
:::panel type="warning"
Right panel
:::
:::
:::
```

### Tables with Inline Plugins

```markdown
| User | Status | Due Date |
|------|--------|----------|
| @john.doe | {status:color=green}Active{/status} | {date:2025-02-01} |
| @jane.smith | {status:color=red}Blocked{/status} | {date:2025-02-15} |
```

## Important Notes

### Limitations

1. **Inline plugins in formatted text**: Plugins inside bold/italic are treated as text
   ```markdown
   **@user** → Bold text "@user", not a mention
   @user in **bold text** → Mention followed by bold text ✓
   ```

2. **Nested block plugins**: Deep nesting of panels/expands may not parse correctly
   ```markdown
   :::panel
   :::expand
   Nested content
   :::
   ::: → May not work as expected
   ```

3. **Table cell content**: Only inline content allowed in table cells
   ```markdown
   | Column |
   |--------|
   | - List | → Won't create a list, just text
   ```

### Best Practices

1. **Spacing**: Leave blank lines between different block elements
2. **Indentation**: Use consistent 2-space indentation for nested lists
3. **Closing markers**: Ensure all block plugins have closing `:::`
4. **Plugin syntax**: Follow exact syntax for inline plugins (case-sensitive)

### Escaping Special Characters

Use backslash to escape:
```markdown
\*not italic\*
\@not-a-mention
\`not code\`
\{not:a:plugin\}
```

## Quick Conversion Test

```python
from mcp_atlassian.formatting.adf_ast import ASTBasedADFGenerator

generator = ASTBasedADFGenerator()
markdown = """
# Test Document

:::panel type="info"
**Status**: {status:color=green}Working{/status}
**Assigned**: @john.doe
:::

Regular paragraph with `code` and [links](https://example.com).
"""

result = generator.markdown_to_adf(markdown)
print(json.dumps(result, indent=2))
```