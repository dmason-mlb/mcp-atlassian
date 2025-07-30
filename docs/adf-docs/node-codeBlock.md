# Node - codeBlock

## Purpose

The codeBlock node is a container for lines of code.

## Type

codeBlock is a top-level block node.

## Example

```json
{
  "type": "codeBlock",
  "attrs": {
    "language": "javascript"
  },
  "content": [
    {
      "type": "text",
      "text": "var foo = {};\nvar bar = [];"
    }
  ]
}
```

## Fields

| Name | Required | Type | Value |
| --- | --- | --- | --- |
| type | ✔ | string | "codeBlock" |
| content | | array | An array of nodes |
| attrs | | object | |
| attrs.language | | string | Language of the code lines |

## Content

content takes an array of one or more text nodes without marks.

## Attributes

* language for syntax highlighting, a code language supported by Prism. See available languages imports for a list of the languages supported in Prism. If set to text or an unsupported value, code is rendered as plain, monospaced text.