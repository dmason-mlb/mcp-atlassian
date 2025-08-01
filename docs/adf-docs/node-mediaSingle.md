# Node - mediaSingle

## Purpose

The mediaSingle node is a container for one media item. This node enables the display of the content in full, in contrast to a mediaGroup that is intended for a list of attachments. A common use case is to display an image, but it can also be used for videos, or other types of content usually renderable by a @atlaskit/media card component.

## Type

mediaSingle is a top-level block node.

## Example

```json
{
  "type": "mediaSingle",
  "attrs": {
    "layout": "center"
  },
  "content": [
    {
      "type": "media",
      "attrs": {
        "id": "4478e39c-cf9b-41d1-ba92-68589487cd75",
        "type": "file",
        "collection": "MediaServicesSample",
        "alt": "moon.jpeg",
        "width": 225,
        "height": 225
      }
    }
  ]
}
```

## Fields

| Name | Required | Type | Value |
| --- | --- | --- | --- |
| type | ✔ | string | "mediaSingle" |
| content | ✔ | array | An array of nodes |
| attrs | ✔ | object | |
| attrs.layout | ✔ | string | "wrap-left", "center", "wrap-right", "wide", "full-width", "align-start", "align-end" |
| attrs.width | | number | Floating point number between 0 and 100 |
| attrs.widthType | | enum | pixel or percentage |

## Content

content must be a media node.

## Attributes

* layout determines the placement of the node on the page. wrap-left and wrap-right provide an image floated to the left or right of the page respectively, with text wrapped around it. center center aligns the image as a block, while wide does the same but bleeds into the margins. full-width makes the image stretch from edge to edge of the page.
* width determines the width of the image as a percentage of the width of the text content area. Has no effect if layout mode is wide or full-width.
* widthType [optional] determines what the "unit" of the width attribute is presenting. Possible values are pixel and percentage. If the widthType attribute is undefined, it fallbacks to percentage.
