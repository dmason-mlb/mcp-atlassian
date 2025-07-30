# Node - orderedList

## Purpose

The orderedList node is a container for a numbered list of items. It's the ordered equivalent of bulletList.

## Type

orderedList is a top-level block node.

## Example

```json
{
  "type": "orderedList",
  "attrs": {
    "order": 3
  },
  "content": [
    {
      "type": "listItem",
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
  ]
}
```

## Fields

| Name | Required | Type | Value |
| --- | --- | --- | --- |
| type | ✔ | string | "orderedList" |
| content | ✔ | array | An array of nodes |
| attrs | | object | |
| attrs.order | | integer | A positive integer greater than or equal to 0 |

## Content

content can contain one or more listItem nodes.

## Attributes

order defines the number of the first item in the list. For example, 3 would mean the list starts at number three. When not specified, the list starts from 1.