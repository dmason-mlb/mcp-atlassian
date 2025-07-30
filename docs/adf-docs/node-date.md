# Node - date

## Purpose

The date node displays a date in the user's locale.

## Type

date is an inline node.

## Example

```json
{
  "type": "date",
  "attrs": {
    "timestamp": "1582152559"
  }
}
```

## Marks

date does not support any marks.

## Fields

| Name | Required | Type | Value |
| --- | --- | --- | --- |
| type | ✔ | string | "date" |
| attrs | ✔ | object | |
| attrs.timestamp | ✔ | string | "" |