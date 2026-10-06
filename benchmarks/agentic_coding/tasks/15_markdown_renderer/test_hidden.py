import unittest
from md import render


class T(unittest.TestCase):
    def r(self, src, exp): self.assertEqual(render(src), exp, repr(src))

    def test_headings(self):
        self.r("# Title", "<h1>Title</h1>"); self.r("###### six", "<h6>six</h6>")
        self.r("####### seven", "<p>####### seven</p>"); self.r("#nospace", "<p>#nospace</p>")
        self.r("## Hello *world*", "<h2>Hello <em>world</em></h2>")

    def test_paragraphs(self):
        self.r("line one\nline two\n\npara two", "<p>line one line two</p>\n<p>para two</p>")
        self.r("  hi  \n  there", "<p>hi there</p>")

    def test_inline(self):
        self.r("This is **bold** and *it* and `co*de*`", "<p>This is <strong>bold</strong> and <em>it</em> and <code>co*de*</code></p>")
        self.r("**a *b* c**", "<p><strong>a <em>b</em> c</strong></p>")

    def test_link(self):
        self.r("See [the **docs**](http://x.com/?a=1&b=2).", '<p>See <a href="http://x.com/?a=1&amp;b=2">the <strong>docs</strong></a>.</p>')

    def test_escape(self):
        self.r("a < b & c > d", "<p>a &lt; b &amp; c &gt; d</p>"); self.r("`<x>`", "<p><code>&lt;x&gt;</code></p>")

    def test_lists(self):
        self.r("- one\n- two\n* three", "<ul><li>one</li><li>two</li><li>three</li></ul>")
        self.r("1. a\n2. b\n10. c", "<ol><li>a</li><li>b</li><li>c</li></ol>")
        self.r("- a\n1. b", "<ul><li>a</li></ul>\n<ol><li>b</li></ol>")
        self.r("- **x**", "<ul><li><strong>x</strong></li></ul>")

    def test_interrupt(self): self.r("para\n- item\n# H", "<p>para</p>\n<ul><li>item</li></ul>\n<h1>H</h1>")

    def test_fence(self):
        self.r("```python\nx = 1 < 2\n**no**\n```\nafter", '<pre><code class="language-python">x = 1 &lt; 2\n**no**</code></pre>\n<p>after</p>')
        self.r("```\na\nb", "<pre><code>a\nb</code></pre>")
        self.r("```\na\n\nb\n```", "<pre><code>a\n\nb</code></pre>")
        self.r("text\n```\ncode\n```", "<p>text</p>\n<pre><code>code</code></pre>")

    def test_blank(self):
        self.r("\n\n# A\n\n\n", "<h1>A</h1>"); self.r("", ""); self.r("   \n  ", "")

    def test_unmatched(self):
        self.r("a ** b", "<p>a ** b</p>"); self.r("*a", "<p>*a</p>"); self.r("[x](", "<p>[x](</p>")
