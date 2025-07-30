# Node - bulletList

## Purpose

The bulletList node is a container for list items.

## Type

bulletList is a top-level block node.

## Example

```json
{
  "type": "bulletList",
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
| type | ✔ | string | "bulletList" |
| content | ✔ | array | An array of nodes |

## Content

content can contain one or more listItem nodes.