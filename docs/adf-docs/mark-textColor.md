# Mark - textColor

## Purpose

The textColor mark sets color styling. This mark applies to text nodes.

## Example

```json
{
  "type": "text",
  "text": "Hello world",
  "marks": [
    {
      "type": "textColor",
      "attrs": {
        "color": "#97a0af"
      }
    }
  ]
}
```

## Combinations with other marks

The textColor cannot be combined with the following marks:

* code
* link

## Rendering colors with theme support

Colors are stored in a hexadecimal format - but need to be displayed differently depending on the current product theme, such as light and dark mode. Support for this is provided via a mapping from each hexadecimal color to a design token from the Atlassian Design System.

Currently, such theming is only supported on web.

This mapping is provided by the @atlaskit/editor-palette package. Documentation for this package is found at https://atlaskit.atlassian.com/packages/editor/editor-palette.

Documentation for Atlassian Design System tokens is found at https://atlassian.design/components/tokens.

## Fields

| Name | Required | Type | Value |
| --- | --- | --- | --- |
| type | ✔ | string | "textColor" |
| attrs | ✔ | object | |
| attrs.color | ✔ | string | A color defined in HTML hexadecimal format, for example #daa520. To display this color with correct contrast in different product themes, such as light and dark mode, use @atlaskit/editor-palette to map this color to a design token from the Atlassian Design System. |
