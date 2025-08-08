# Node - tableCell

## Purpose

The tableCell node defines a cell within a table row.

Note: only supported on web and desktop. Mobile rendering support for tables is not available.

## Type

tableCell is a child block node of the tableRow node.

## Example

```json
{
  "type": "tableCell",
  "attrs": {},
  "content": [
    {
      "type": "paragraph",
      "content": [
        {
          "type": "text",
          "text": "Hello world"
        }
      ]
    }
  ]
}
```

## Fields

| Name | Required | Type | Value |
| --- | --- | --- | --- |
| type | ✔ | string | "tableCell" |
| content | ✔ | array | An array of one or more nodes |
| attrs | | object | |
| attrs.background | | string | Short or long hex color code or HTML color name |
| attrs.colspan | | integer | Positive integer, defaults to 1 |
| attrs.colwidth | | array | Array of positive integers |
| attrs.rowspan | | integer | Positive integer, defaults to 1 |

## Content

content takes an array of one or more of these nodes:

* blockquote
* bulletList
* codeBlock
* heading
* mediaGroup
* nestedExpand
* orderedList
* panel
* paragraph
* rule

## Attributes

* background defines the color of the cell background.
* colspan defines the number of columns the cell spans.
* colwidth defines the width of the column or, where the cell spans columns, the width of the columns it spans in pixels. The length of the array should be equal to the number of spanned columns. 0 is permitted as an array value if the column size is not fixed, for example, a cell merged across 3 columns where one unfixed column is surrounded by two fixed might be represented as `[120, 0, 120]`.
* rowspan defines the number of rows a cell spans.
