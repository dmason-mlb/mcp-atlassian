# Atlassian Document Format - Structure

## Purpose

The Atlassian Document Format (ADF) represents rich text stored in Atlassian products. For example, in Jira Cloud platform, the text in issue comments and in textarea custom fields is stored as ADF.

## JSON schema

An Atlassian Document Format document is a JSON object. A JSON schema is available to validate documents. This JSON schema is found at http://go.atlassian.com/adf-json-schema.

Marks and nodes included in the JSON schema may not be valid in this implementation. Refer to this documentation for details of supported marks and nodes.

## JSON structure

An ADF document is composed of a hierarchy of nodes. There are two categories of nodes: block and inline. Block nodes define the structural elements of the document such as headings, paragraphs, lists, and alike. Inline nodes contain the document content such as text and images. Some of these nodes can take marks that define text formatting or embellishment such as centered, bold, italics, and alike.

To center text: add a mark of the type alignment with an attribute align and the value center.

A document is ordered, that is, there's a single sequential path through it: traversing a document in sequence and concatenating the nodes yields content in the correct order.

For example:

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
          "text": "Hello "
        },
        {
          "type": "text",
          "text": "world",
          "marks": [
            {
              "type": "strong"
            }
          ]
        }
      ]
    }
  ]
}
```

Result in the text "Hello **world**".

## Nodes

Nodes have the following common properties:

| Property | Required | Description |
| --- | --- | --- |
| type | ✔ | Defines the type of block node such as paragraph, table, and alike. |
| content | ✔ in block nodes, not applicable in inline nodes | An array containing inline and block nodes that define the content of a section of the document. |
| version | ✔ in the root, otherwise not applicable | Defines the version of ADF used in this representation. |
| marks | | Defines text decoration or formatting. |
| attrs | | Further information defining attributes of the block such as the language represented in a block of code. |

### Block nodes

Block nodes can be subdivided into:

* the root (doc) node.
* top level nodes, nodes that can be placed directly below the root node.
* child nodes, nodes that have to be the child of a higher-level mode.

Some top-level nodes can be used as child nodes. For example, the paragraph node can be used at the top level or embedded within a list or table.

#### Root block node

Every document starts with a root doc node. This node contains the version and content properties. The simplest document in ADF is this root node with no content:

```json
{
  "version": 1,
  "type": "doc",
  "content": []
}
```

### Top-level block nodes

The top-level block nodes include:

* blockquote
* bulletList
* codeBlock
* expand
* heading
* mediaGroup
* mediaSingle
* orderedList
* panel
* paragraph
* rule
* table
* multiBodiedExtension

### Child block nodes

The child block nodes include:

* listItem
* media
* nestedExpand
* tableCell
* tableHeader
* tableRow
* extensionFrame

## Inline nodes

The inline nodes include:

* date
* emoji
* hardBreak
* inlineCard
* mention
* status
* text
* mediaInline

## Marks

Mark have the following properties:

| Property | Required | Description |
| --- | --- | --- |
| type | ✔ | Defines the type of mark such as code, link, and alike. |
| attrs | | Further information defining attributes of the mask such as the URL in a link. |

The marks include:

* border
* code
* em
* link
* strike
* strong
* subsup
* textColor
* underline