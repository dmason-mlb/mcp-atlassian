# Client libraries

## Javascript

The adf-builder client library for JavaScript offers two ways to build documents:

* A fluent document builder interface, with support for all node types.
* A tag to be used with ES6 template literals, for single-paragraph documents.

To import the library use:

```bash
npm install adf-builder
```

See Atlassian Document Format Builder (JavaScript) for more detailed documentation.

Example:

```javascript
var { Document } = require('adf-builder');

const doc = new Document();

doc.paragraph()
  .text('Here is some ')
  .strong('bold test')
  .text(' and ')
  .em('text in italics')
  .text(' as well as ')
  .link(' a link', 'https://www.atlassian.com')
  .text(' , emojis ')
  .emoji(':smile:')
  .emoji(':rofl:')
  .emoji(':nerd:')
  .text(' and some code: ')
  .code('var i = 0;')
  .text(' and a bullet list');

doc.bulletList()
  .textItem('With one bullet point')
  .textItem('And another');

doc.panel("info")
  .paragraph()
  .text("and an info panel with some text, with some more code below");

doc.codeBlock("javascript")
  .text('var i = 0;\nwhile(true) {\n  i++;\n}');

var reply = doc.toJSON();
```

## Java

The adf-builder-java client library provides a fluent document builder. Additional modules, such as adf-builder-java-jackson2 are available to provide JSON support.

See the Quick Start Guide for more information.

Example:

```java
import com.atlassian.adf.jackson2.AdfJackson2;
import com.atlassian.adf.model.node.Doc;

import static com.atlassian.adf.model.mark.Strong.strong;
import static com.atlassian.adf.model.node.Doc.doc;
import static com.atlassian.adf.model.node.Paragraph.p;
import static com.atlassian.adf.model.node.Rule.hr;
import static com.atlassian.adf.model.node.Text.text;

public class Example {
    public static void main(String[] args) {
        Doc doc = doc(
            p("Hello"),
            hr(),
            p(
                text("world", strong()),
                text("!")
            )
        );

        AdfJackson2 parser = new AdfJackson2();
        String json = parser.marshall(doc);
        System.out.println(json);

        Doc reconstructed = parser.unmarshall(json);
        if (!doc.equals(reconstructed)) {
            throw new AssertionError("Hmmmm... they should have matched...");
        }
    }
}
```

## Kotlin

The adf-builder-java Java library was designed to work well in Kotlin directly. In particular:

* Statics and the roots of fluid builders have distinctive names like emoji rather than just builder so that they can all peacefully coexist in the same namespace.
* Nullability handling is strict by default and fully annotated so that the Kotlin compiler knows exactly where null inputs are tolerated.

One small drawback is that the Java library uses Optional wrappers instead of a @Nullable annotation for optional return values. Kotlin code will generally need to unwrap these values with .getOrNull() to reach a more idiomatic data type for that language.

Example:

```kotlin
val doc = Doc.doc(
    p("Hello"),
    hr,
    p(
        text("world", strong()),
        text("!")
    )
)
```
