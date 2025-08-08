# Node - emoji

## Purpose

The emoji node is an inline node that represents an emoji.

There are three kinds of emoji:

* Standard — Unicode emoji
* Atlassian — Non-standard emoji introduced by Atlassian
* Site — Non-standard customer defined emoji

## Type

emoji is an inline node.

## Examples

### Unicode emoji

```json
{
  "type": "emoji",
  "attrs": {
    "shortName": ":grinning:",
    "text": "😀"
  }
}
```

### Non-standard Atlassian emoji

```json
{
  "type": "emoji",
  "attrs": {
    "shortName": ":awthanks:",
    "id": "atlassian-awthanks",
    "text": ":awthanks:"
  }
}
```

### Non-standard customer emoji

```json
{
  "type": "emoji",
  "attrs": {
    "shortName": ":thumbsup::skin-tone-2:",
    "id": "1f44d",
    "text": "👍🏽"
  }
}
```

## Fields

| Name | Required | Type | Value |
| --- | --- | --- | --- |
| type | ✔ | string | "emoji" |
| attrs | ✔ | object | |
| attrs.id | | string | Emoji service ID of the emoji |
| attrs.shortName | ✔ | string | |
| attrs.text | | string | |

## Attributes

* id is the Emoji service ID of the emoji. The value varies based on the kind, for example, standard emoji ID "1f3f3-1f308", Atlassian emoji ID "— "atlassian-<shortName>", and site emoji ID " "13d29267-ff9e-4892-a484-1a1eef3b5ca3". The value is not intended to have any user facing meaning.
* shortName represent a name for the emoji, such as ":grinning:"
* text represents the text version of the emoji, shortName is rendered instead if omitted. more
