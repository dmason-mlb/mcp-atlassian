# Node - status

## Purpose

The status node is a mutable inline node that represents the state of work.

## Examples

```json
{
  "type": "status",
  "attrs": {
    "localId": "abcdef12-abcd-abcd-abcd-abcdef123456",
    "text": "In Progress",
    "color": "yellow"
  }
}
```

## Content

status is an inline node in the inlines group.

## Marks

status does not support any marks.

## Fields

| Name | Required | Type | Value | Notes |
| --- | --- | --- | --- | --- |
| type | ✔ | string | "status" | |
| attrs | ✔ | object | | |
| attrs.localId | | string | | unique identifier, auto-generated |
| attrs.text | ✔ | string | | The textual representation of the status |
| attrs.color | ✔ | string | "neutral" \| "purple" \| "blue"\| "red"\| "yellow"\| "green" | neutral is the default and represents the grey color |
