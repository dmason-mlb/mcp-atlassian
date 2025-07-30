# Mark - code

## Purpose

The code mark sets code styling. This mark applies to text nodes.

## Example

```json
{
  "type": "text",
  "text": "Hello world",
  "marks": [
    {
      "type": "code"
    }
  ]
}
```

## Combinations with other marks

code can ONLY be combined with the following marks:

* link

## Fields

| Name | Required | Type | Value |
| --- | --- | --- | --- |
| type | ✔ | string | "code" |