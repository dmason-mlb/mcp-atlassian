# Node - nestedExpand

## Purpose

The nestedExpand node is a container that allows content to be hidden or shown, similar to an accordion or disclosure widget.

nestedExpand is available to avoid infinite nesting, therefore it can only be placed within a TableCell or TableHeader, where an Expand can only be placed at the top-level or inside a .

## Example

```json
{
  "type": "nestedExpand",
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

## Content

nestedExpand can contain an array of one-or-more:

* Paragraph
* Heading
* MediaGroup
* MediaSingle

## Fields

| Name | Required | Type | Value | Notes |
| --- | --- | --- | --- | --- |
| content | ✔ | | Array of one-or-more above mentioned nodes. | |
| type | ✔ | string | "nestedExpand" | |
| attrs | ✔ | object | | |
| attrs.title | | string | | |
