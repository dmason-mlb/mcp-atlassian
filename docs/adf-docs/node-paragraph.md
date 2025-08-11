# Node - paragraph

## Purpose

The paragraph node is a container for a block of formatted text delineated by a carriage return. It's the equivalent of the HTML <p> tag.

## Type

paragraph is a top-level block node.

## Example

```json
{
  "type": "paragraph",
  "content": [
    {
      "type": "text",
      "text": "Hello world"
    }
  ]
}
```

## Fields

| Name | Required | Type | Value |
| --- | --- | --- | --- |
| type | ✔ | string | "paragraph" |
| content | | array | Array of zero or more nodes. |
| attrs | | object | |
| attrs.localId | | string | An ID to uniquely identify this node within the document. |

## Content

content can take any inline mode.
