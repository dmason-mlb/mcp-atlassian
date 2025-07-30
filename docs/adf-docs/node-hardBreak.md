# Node - hardBreak

## Purpose

The hardBreak node inserts a new line in a text string. It's the equivalent to a <br/> in HTML.

## Type

hardBreak is an inline node.

## Example

```json
{
  "version": 1,
  "type": "doc",
  "content": [
    {
      "type": "paragraph",
      "content": [
        {
          "type": "text",
          "text": "Hello"
        },
        {
          "type": "hardBreak"
        },
        {
          "type": "text",
          "text": "world"
        }
      ]
    }
  ]
}
```

## Fields

| Name | Required | Type | Value |
| --- | --- | --- | --- |
| type | ✔ | string | "hardBreak" |
| attrs | | object | |
| attrs.text | | string | "\n" |