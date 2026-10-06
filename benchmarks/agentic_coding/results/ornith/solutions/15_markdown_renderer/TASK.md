Create `md.py` with `render(text: str) -> str`, converting a Markdown subset to HTML. Output blocks are joined with
`"\n"` (no trailing newline); an empty/blank document renders to `""`.

Block rules (process line by line; markers are at column 0):
1. Fenced code: a line starting with three backticks opens a block (optional language word after them); it closes at the next
   line that is exactly three backticks (ignoring trailing whitespace) or at end of document. Content lines are HTML-escaped and
   joined with `\n`: `<pre><code>CONTENT</code></pre>`, or `<pre><code class="language-LANG">CONTENT</code></pre>` if a language is given.
   No inline formatting inside code blocks.
2. Heading: 1-6 `#` followed by a space: `<hN>INLINE</hN>` (text stripped). `#######` or `#x` are not headings.
3. Unordered list: consecutive lines starting with `- ` or `* ` -> `<ul><li>INLINE</li>...</ul>` on one line.
4. Ordered list: consecutive lines matching `<digits>. ` -> `<ol><li>INLINE</li>...</ol>` on one line. Switching between `ul`
   and `ol` lines starts a new list.
5. Blank lines separate blocks.
6. Paragraph: consecutive other non-blank lines, each stripped, joined by a single space: `<p>INLINE</p>`. A heading, list item
   or fence line ends the paragraph (and starts its own block).

Inline rules (headings, list items, paragraphs):
- HTML-escape `&`, `<`, `>` in text.
- Code spans `` `code` `` -> `<code>code</code>` (content escaped, no further formatting inside).
- Links `[text](url)` -> `<a href="url">text</a>` (text gets bold/italic formatting; in the url escape `&` as `&amp;` and `"` as `&quot;`).
- `**x**` -> `<strong>x</strong>`, then `*x*` -> `<em>x</em>`, where x is non-empty and does not start or end with whitespace.
- Unmatched markers stay literal.
