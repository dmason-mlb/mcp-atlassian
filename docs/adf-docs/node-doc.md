# Node - doc

## Purpose

The doc node is the root container node representing a document.

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
| type | ✔ | string | "doc" |
| content | ✔ | array | An array of zero or more nodes. |
| version | ✔ | integer | 1 |

## Content

content takes zero or more top-level block nodes.

## Version

version represents the version of the ADF specification used in the document.
