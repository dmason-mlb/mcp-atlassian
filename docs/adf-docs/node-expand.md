# Node - expand

## Purpose

The expand node is a container that enables content to be hidden or shown, similar to an accordion or disclosure widget.

Note: To add an expand to a table (tableCell or tableHeader) use nestedExpand instead.

## Type

expand is a top-level block node.

## Example

```json
{
  "type": "expand",
  "attrs": {
    "title": "Hello world"
  },
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
| type | ✔ | string | "expand". |
| content | ✔ | array | Array of one or more nodes. |
| attrs | ✔ | object | |
| attrs.title | | string | A title for the expand. |
| marks | | array | An optional mark. |

## Content

expand takes an array of one or more of the following nodes:

* bulletList
* blockquote
* codeblock
* heading
* mediaGroup
* mediaSingle
* orderedList
* panel
* paragraph
* rule
* table
* multiBodiedExtension
* extensionFrame
* nestedExpand
