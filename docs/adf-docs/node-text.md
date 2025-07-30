# Node - text

## Purpose

The text node holds document text.

## Type

text is an inline node.

## Example

```json
{
  "type": "text",
  "text": "Hello world"
}
```

## Fields

| Name | Required | Type | Value |
| --- | --- | --- | --- |
| type | ✔ | string | "text" |
| text | ✔ | string | Non-empty text string |
| marks | | array | Array of marks |

## Text

text must not be empty.

## Marks

The following marks can be applied:

* code
* em
* link
* strike
* strong
* subsup
* textColor
* underline