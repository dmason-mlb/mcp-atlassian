# Mark - backgroundColor

## Purpose

The backgroundColor mark sets background color styling. This mark applies to text nodes.

## Example

```json
{
  "type": "text",
  "text": "Hello world",
  "marks": [
    {
      "type": "backgroundColor",
      "attrs": {
        "color": "#fedec8"
      }
    }
  ]
}
```

## Combinations with other marks

The backgroundColor cannot be combined with the following marks:

* code

## Rendering colors with theme support

Colors are stored in a hexadecimal format - but need to be displayed differently depending on the current product theme, such as light and dark mode. Support for this is provided via a mapping from each hexadecimal color to a design token from the Atlassian Design System.

Currently, such theming is only supported on web.

This mapping is provided by the @atlaskit/editor-palette package. Documentation for this package is found at https://atlaskit.atlassian.com/packages/editor/editor-palette.

Documentation for Atlassian Design System tokens is found at https://atlassian.design/components/tokens.

## Fields

| Name | Required | Type | Value |
| --- | --- | --- | --- |
| type | ✔ | string | "backgroundColor" |
| attrs | ✔ | object | |
| attrs.color | ✔ | string | A color defined in HTML hexadecimal format, for example #daa520. To display this color with correct contrast in different product themes, such as light and dark mode, use colors defined in the background color palette of @atlaskit/editor-palette. |
