# Node - table

## Purpose

The table node provides a container for the nodes that define a table.

Note: only supported on web and desktop. Mobile rendering support for tables is not available.

## Type

table is a top-level block node.

## Example

```json
{
  "type": "table",
  "attrs": {
    "isNumberColumnEnabled": false,
    "layout": "center",
    "width": 900,
    "displayMode": "default"
  },
  "content": [
    {
      "type": "tableRow",
      "content": [
        {
          "type": "tableCell",
          "attrs": {},
          "content": [
            {
              "type": "paragraph",
              "content": [
                {
                  "type": "text",
                  "text": " Row one, cell one"
                }
              ]
            }
          ]
        },
        {
          "type": "tableCell",
          "attrs": {},
          "content": [
            {
              "type": "paragraph",
              "content": [
                {
                  "type": "text",
                  "text": "Row one, cell two"
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

## Fields

| Name | Required | Type | Value |
| --- | --- | --- | --- |
| type | ✔ | string | "table" |
| content | ✔ | array | Array of one or more nodes |
| attrs | | object | |
| attrs.isNumberColumnEnabled | | boolean | 'true','false' |
| attrs.width | | number | A positive integer |
| attrs.layout | | string | 'center', 'align-start' |
| attrs.displayMode | | string | 'default', 'fixed' |

## Content

content takes an array of one or more tableRow nodes.

## Attributes

When isNumberColumnEnabled is set to 'true' the first table column provides numbering for the table rows.

width sets the length (in pixels) of the table on the page. This value is independent of the table's column width, this allows control of the table's overflow. It supersedes the existing layout attribute and will be used instead of it at runtime. If width is not provided the editor will convert layout to pixels (default=760, wide=960 and full-width=1800). Although no minimum and maximum width is enforced it is recommended to follow these guidelines:

Minimum width

* 1 column table = 48px
* 2 column table = 96px
* 3 column table = 144px
* > 3 column table = 144px

Maximum width

* 1800

layout determines the alignment of a table in the full page editor, relevant to the line length. Currently only center and left alignment options are supported.

The layout values are mapped as follows:

* center will align the table to the center of page, its width can be larger than the line length
* align-start will align the table left of the line length, its width cannot be larger than the line length

The layout attribute was previously reserved for width options ('default', 'wide' and 'full-width') however this was deprecated when the width attribute was released and should be used instead. The editor continues to convert these values to widths, but if you wish to apply an alignment value please use width and layout for table alignment.

These settings do not apply in Jira where tables are automatically displayed across the full width of the text container.

displayMode attribute controls how tables adapt to narrow screens:

* When displayMode is set to 'default' or left unset, the table's columns will automatically scale down to accommodate narrow screens, with a maximum reduction of up to 40%.
* When displayMode is set to 'fixed', the table's columns will maintain their original width, regardless of screen size.