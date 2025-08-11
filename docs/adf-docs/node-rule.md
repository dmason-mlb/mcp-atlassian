# Node - rule

## Purpose

The rule node represents a divider, it is equivalent to the HTML <hr/> tag.

## Type

rule is a top-level block node.

## Example

```json
{
  "version": 1,
  "type": "doc",
  "content": [
    {
      "type": "paragraph",
      "content": [
        {
          "type": "text",
          "text": "Hello world"
        }
      ]
    },
    {
      "type": "rule"
    }
  ]
}
```

## Fields

| Name | Required | Type | Value |
| --- | --- | --- | --- |
| type | ✔ | string | "rule" |
