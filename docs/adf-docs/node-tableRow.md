# Node - tableRow

## Purpose

The tableRow node defines rows within a table and is a container for table heading and table cell nodes.

Note: only supported on web and desktop. Mobile rendering support for tables is not available.

## Type

tableRow is a child block node of the table node.

## Example

```json
{
  "type": "tableRow",
  "content": [
    {
      "type": "tableHeader",
      "attrs": {},
      "content": [
        {
          "type": "paragraph",
          "content": [
            {
              "type": "text",
              "text": "Heading one",
              "marks": [
                {
                  "type": "strong"
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
| type | ✔ | string | "tableRow" |
| content | ✔ | array | An array of nodes |

## Content

content takes an array of one or more tableHeader or tableCell nodes.
