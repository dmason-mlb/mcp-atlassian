# Mark - link

## Purpose

The link mark sets a hyperlink. This mark applies to text nodes.

## Example

```json
{
  "type": "text",
  "text": "Hello world",
  "marks": [
    {
      "type": "link",
      "attrs": {
        "href": "http://atlassian.com",
        "title": "Atlassian"
      }
    }
  ]
}
```

## Fields

| Name | Required | Type | Value |
| --- | --- | --- | --- |
| type | ✔ | string | "link" |
| attrs | ✔ | object | |
| attrs.collection | | string | |
| attrs.href | ✔ | string | A URI |
| attrs.id | | string | |
| attrs.occurrenceKey | | string | |
| attrs.title | | string | Title for the URI |

## Attributes

* collection
* href defines the URL for the hyperlink and is the equivalent of the href value for a HTML <a> element.
* id
* occurrenceKey
* title defines the title for the hyperlink and is the equivalent of the title value for a HTML <a> element.