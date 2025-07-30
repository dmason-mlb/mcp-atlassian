# Node - listItem

## Purpose

The listItem node represents an item in a list.

## Type

listItem is a child block node of:

* bulletList
* orderedList

## Example

```json
{
  "type": "listItem",
  "content": [
    {
      "type": "paragraph",
      "content": [
        {
          "type": "text",
          "text": "Hello world"
        }
      ]
    }
  ]
}
```

## Fields

| Name | Required | Type | Value |
| --- | --- | --- | --- |
| type | ✔ | string | "listItem" |
| content | ✔ | array | An array of one or more nodes. |

## Content

content must contain at least one of the following nodes:

* bulletList
* codeBlock with no marks
* mediaSingle
* orderedList
* paragraph with no marks