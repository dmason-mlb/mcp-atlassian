# Node - panel

## Purpose

The panel node is a container that highlights content.

## Type

panel is a top-level block node.

## Example

```json
{
  "type": "panel",
  "attrs": {
    "panelType": "info"
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
| type | ✔ | string | "panel" |
| content | ✔ | array | An array of one or more nodes |
| attrs | ✔ | object | |
| attrs.panelType | ✔ | string | "info", "note", "warning", "success", "error" |

## Content

content must contain array of one or more of the following nodes:

* bulletList
* heading with no marks.
* orderedList
* paragraph with no marks.
