# Node - heading

## Purpose

The heading node represents a heading.

## Content

heading is a top-level block node.

## Example

```json
{
  "type": "heading",
  "attrs": {
    "level": 1
  },
  "content": [
    {
      "type": "text",
      "text": "Heading 1"
    }
  ]
}
```

## Fields

| Name | Required | Type | Value |
| --- | --- | --- | --- |
| type | ✔ | string | "heading" |
| content | | array | Array of zero or more inline nodes |
| attrs | ✔ | object | |
| attrs.level | ✔ | integer | 1-6 |
| attrs.localId | | string | An ID to uniquely identify this node within the document. |

## Content

content takes any inline node.

## Attributes

* level represents the depth of the heading following the same convention as HTML: when level is set to 1 it's the equivalent of <h1>.
