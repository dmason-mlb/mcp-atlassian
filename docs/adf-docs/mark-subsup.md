# Mark - subsup

## Purpose

The subsup mark sets ^superscript or _subscript styling. This mark applies to text nodes.

## Example

```json
{
  "type": "text",
  "text": "Hello world",
  "marks": [
    {
      "type": "subsup",
      "attrs": {
        "type": "sub"
      }
    }
  ]
}
```

## Fields

| Name | Required | Type | Value |
| --- | --- | --- | --- |
| type | ✔ | string | "subsup" |
| attrs | ✔ | object | |
| attrs.type | ✔ | string | "sup" or "sub" |