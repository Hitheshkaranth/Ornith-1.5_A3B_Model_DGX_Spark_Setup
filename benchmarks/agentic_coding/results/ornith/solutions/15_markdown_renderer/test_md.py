import unittest

from md import render


class RenderTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(render(""), "")
        self.assertEqual(render("\n\n"), "")
        self.assertEqual(render("   \n  \n"), "")

    def test_plain_paragraph(self):
        self.assertEqual(render("hello"), "<p>hello</p>")

    def test_paragraph_join(self):
        self.assertEqual(render("a\nb"), "<p>a b</p>")
        self.assertEqual(render("a\n  b\n   c"), "<p>a b c</p>")

    def test_blank_separates(self):
        self.assertEqual(render("a\n\nb"), "<p>a</p>\n<p>b</p>")

    def test_heading(self):
        self.assertEqual(render("# H"), "<h1>H</h1>")
        self.assertEqual(render("## H"), "<h2>H</h2>")
        self.assertEqual(render("###### H"), "<h6>H</h6>")

    def test_not_heading(self):
        self.assertEqual(render("####### x"), "<p>####### x</p>")
        self.assertEqual(render("#x"), "<p>#x</p>")
        self.assertEqual(render("#######x"), "<p>#######x</p>")

    def test_code_block_plain(self):
        self.assertEqual(render("```\ncode\nhere\n```"),
                         "<pre><code>code\nhere</code></pre>")

    def test_code_block_lang(self):
        self.assertEqual(render("```python\nx=1\n```"),
                         '<pre><code class="language-python">x=1</code></pre>')

    def test_code_block_escaped(self):
        self.assertEqual(render("```\n<b>&\n```"),
                         "<pre><code>&lt;b&gt;&amp;</code></pre>")

    def test_code_block_no_close(self):
        self.assertEqual(render("```\nopen"), "<pre><code>open</code></pre>")

    def test_code_block_trailing_ws_close(self):
        self.assertEqual(render("```\nq\n```   "), "<pre><code>q</code></pre>")

    def test_escaping(self):
        self.assertEqual(render("a & b"), "<p>a &amp; b</p>")
        self.assertEqual(render("<tag>"), "<p>&lt;tag&gt;</p>")

    def test_code_span(self):
        self.assertEqual(render("`code`"), "<p><code>code</code></p>")
        self.assertEqual(render("`a<b&`"), "<p><code>a&lt;b&amp;</code></p>")
        self.assertEqual(render("before `"), "<p>before `</p>")

    def test_code_span_unmatched(self):
        self.assertEqual(render("`unclosed"), "<p>`unclosed</p>")

    def test_link(self):
        self.assertEqual(render("[text](http://x)"),
                         '<p><a href="http://x">text</a></p>')

    def test_link_url_escaping(self):
        self.assertEqual(render("[t](a&b)"), '<p><a href="a&amp;b">t</a></p>')
        self.assertEqual(render('[t](a"b)'), '<p><a href="a&quot;b">t</a></p>')

    def test_link_text_formatted(self):
        self.assertEqual(render("[**b**](u)"),
                         '<p><a href="u"><strong>b</strong></a></p>')

    def test_link_plain_brackets(self):
        self.assertEqual(render("just [brackets]"), "<p>just [brackets]</p>")

    def test_bold(self):
        self.assertEqual(render("**x**"), "<p><strong>x</strong></p>")

    def test_italic(self):
        self.assertEqual(render("*x*"), "<p><em>x</em></p>")

    def test_bold_then_italic_independent(self):
        self.assertEqual(render("**a** and *b*"),
                         "<p><strong>a</strong> and <em>b</em></p>")

    def test_unmatched_markers(self):
        self.assertEqual(render("*x"), "<p>*x</p>")
        self.assertEqual(render("x*"), "<p>x*</p>")
        self.assertEqual(render("**x"), "<p>**x</p>")

    def test_no_space_emphasis(self):
        self.assertEqual(render("a * x * b"), "<p>a * x * b</p>")
        self.assertEqual(render("a *  * b"), "<p>a *  * b</p>")

    def test_inline_mixed(self):
        self.assertEqual(render("**bold** and *italic* and `c` and [l](u)"),
                         '<p><strong>bold</strong> and <em>italic</em> and '
                         '<code>c</code> and <a href="u">l</a></p>')

    def test_ul(self):
        self.assertEqual(render("- a\n- b"), "<ul><li>a</li><li>b</li></ul>")
        self.assertEqual(render("* a\n* b"), "<ul><li>a</li><li>b</li></ul>")

    def test_ul_mixed_markers(self):
        self.assertEqual(render("- a\n* b"), "<ul><li>a</li><li>b</li></ul>")

    def test_ol(self):
        self.assertEqual(render("1. a\n2. b"),
                         "<ol><li>a</li><li>b</li></ol>")

    def test_ol_multi_digit(self):
        self.assertEqual(render("10. a"), "<ol><li>a</li></ol>")

    def test_list_switch(self):
        self.assertEqual(render("- a\n1. b"),
                         "<ul><li>a</li></ul>\n<ol><li>b</li></ol>")

    def test_list_then_paragraph(self):
        self.assertEqual(render("- a\nplain"), "<ul><li>a</li></ul>\n<p>plain</p>")

    def test_list_then_heading(self):
        self.assertEqual(render("- a\n## H"), "<ul><li>a</li></ul>\n<h2>H</h2>")

    def test_paragraph_then_list(self):
        self.assertEqual(render("plain\n- a"), "<p>plain</p>\n<ul><li>a</li></ul>")

    def test_item_with_inline(self):
        self.assertEqual(render("- **b**"), "<ul><li><strong>b</strong></li></ul>")

    def test_list_blank_breaks(self):
        self.assertEqual(render("- a\n\n- b"),
                         "<ul><li>a</li></ul>\n<ul><li>b</li></ul>")

    def test_needs_space(self):
        self.assertEqual(render("-x"), "<p>-x</p>")
        self.assertEqual(render("1.x"), "<p>1.x</p>")
        self.assertEqual(render("#x"), "<p>#x</p>")

    def test_crlf(self):
        self.assertEqual(render("a\r\nb"), "<p>a b</p>")

    def test_paragraph_then_heading(self):
        self.assertEqual(render("para\n## H"), "<p>para</p>\n<h2>H</h2>")

    def test_code_block_ends_paragraph(self):
        self.assertEqual(render("para\n```\nx\n```"),
                         "<p>para</p>\n<pre><code>x</code></pre>")

    def test_heading_content_escaped(self):
        self.assertEqual(render("# a & b"), "<h1>a &amp; b</h1>")

    def test_multi_blocks(self):
        doc = "# H\n\npara one\npara two\n\n- a\n- b\n\n```\ncode\n```\n"
        expected = ("<h1>H</h1>\n<p>para one para two</p>\n"
                    "<ul><li>a</li><li>b</li></ul>\n"
                    '<pre><code>code</code></pre>')
        self.assertEqual(render(doc), expected)


if __name__ == "__main__":
    unittest.main()