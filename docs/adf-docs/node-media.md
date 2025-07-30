# Node - media

## Purpose

The media node represents a single file or link stored in media services.

## Type

media is a child block node of:

* mediaGroup
* mediaSingle

## Example

```json
{
  "type": "media",
  "attrs": {
    "id": "4478e39c-cf9b-41d1-ba92-68589487cd75",
    "type": "file",
    "collection": "MediaServicesSample",
    "alt": "moon.jpeg",
    "width": 225,
    "height": 225
  },
  "marks": [
    {
      "type": "link",
      "attrs": {
        "href": "https://developer.atlassian.com/platform/atlassian-document-format/concepts/document-structure/nodes/media/#media"
      }
    },
    {
      "type": "border",
      "attrs": {
        "color": "#091e4224",
        "size": 2
      }
    },
    {
      "type": "annotation",
      "attrs": {
        "id": "c4cbe18e-9902-4734-bf9b-1426a81ef785",
        "annotationType": "inlineComment"
      }
    }
  ]
}
```

## Fields

| Name | Required | Type | Value |
| --- | --- | --- | --- |
| type | ✔ | string | "media" |
| attrs | ✔ | object | |
| attrs.width | | integer | A positive integer |
| attrs.height | | integer | A positive integer |
| attrs.id | ✔ | string | Media Services ID |
| attrs.type | ✔ | string | "file", "link" |
| attrs.collection | ✔ | string | Media Services Collection name |
| attrs.occurrenceKey | | string | Non—empty string |

## Attributes

* width defines the display width of the media item in pixels. Must be provided within mediaSingle or the media isn't displayed.
* height defines the display height of the media item in pixels. Must be provided within mediaSingle or the media isn't displayed.
* id is the Media Services ID and is used for querying the media services API to retrieve metadata, such as, filename. Consumers of the document should always fetch fresh metadata using the Media API.
* type whether the media is a file or a link.
* collection the Media Services Collection name for the media.
* occurrenceKey needs to be present in order to enable deletion of files from a collection.

## Marks

The following marks can be applied:

* border
* link