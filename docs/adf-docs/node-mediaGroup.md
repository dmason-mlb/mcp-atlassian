# Node - mediaGroup

## Purpose

The mediaGroup node is a container for several media items. Compare to mediaSingle, which is intended for the display of a single media item in full.

## Type

mediaGroup is a top-level block node.

## Example

```json
{
  "type": "mediaGroup",
  "content": [
    {
      "type": "media",
      "attrs": {
        "type": "file",
        "id": "6e7c7f2c-dd7a-499c-bceb-6f32bfbf30b5",
        "collection": "ae730abd-a389-46a7-90eb-c03e75a45bf6"
      }
    },
    {
      "type": "media",
      "attrs": {
        "type": "file",
        "id": "6e7c7f2c-dd7a-499c-bceb-6f32bfbf30b5",
        "collection": "ae730abd-a389-46a7-90eb-c03e75a45bf6"
      }
    }
  ]
}
```

## Fields

| Name | Required | Type | Value |
| --- | --- | --- | --- |
| type | ✔ | string | "mediaGroup" |
| content | ✔ | array | An array of nodes |

## Content

content must contain one or more media nodes.