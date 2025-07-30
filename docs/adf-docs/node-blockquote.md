# Node - blockquote

## Purpose

The blockquote node is a container for quotes.

## Type

blockquote is a top-level block node.

## Example

```json
{
  "type": "blockquote",
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
| type | ✔ | string | "blockquote" |
| content | ✔ | array | An array of nodes |

## Content

content must contain array of one or more of the following nodes:

* paragraph with no marks.
* bulletList
* orderedList
* codeBlock
* mediaGroup
* mediaSingle