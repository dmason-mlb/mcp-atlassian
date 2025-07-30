# Node - mention

## Purpose

The mention node represents a user mention.

## Type

mention is an inline node.

## Examples

```json
{
  "type": "mention",
  "attrs": {
    "id": "ABCDE-ABCDE-ABCDE-ABCDE",
    "text": "@Bradley Ayers",
    "userType": "APP"
  }
}
```

## Fields

| Name | Required | Type | Value |
| --- | --- | --- | --- |
| type | ✔ | string | "mention" |
| attrs | ✔ | object | |
| attrs.accessLevel | | string | "NONE", "SITE", "APPLICATION", "CONTAINER" |
| attrs.id | ✔ | string | Atlassian Account ID or collection name |
| attrs.text | | string | |
| attrs.userType | | string | "DEFAULT", "SPECIAL", "APP" |

## Attributes

* accessLevel
* id the Atlassian account ID or collection name of the person or collection being mentioned.
* text the textual representation of the mention, including a leading @.
* userType