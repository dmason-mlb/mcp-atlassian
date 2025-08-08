# Node - inlineCard

## Purpose

The inlineCard node is an Atlassian link card with a type icon and content description derived from the link.

## Type

inlineCard is an inline node.

## Example

```json
{
  "type": "inlineCard",
  "attrs": {
    "url": "https://atlassian.com"
  }
}
```

## Fields

| Name | Required | Type | Value |
| --- | --- | --- | --- |
| type | ✔ | string | "inlineCard" |
| attrs | ✔ | object | |
| attrs.data | | object | JSONLD representation of the link |
| attrs.url | | object | A URI |

## Attributes

Either data or url must be provided, but not both.
