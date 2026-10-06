import unittest

import csvparse


class ParseTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(csvparse.parse_csv(""), [])

    def test_simple_fields(self):
        self.assertEqual(csvparse.parse_csv("a,b,c"), [["a", "b", "c"]])

    def test_single_field_no_newline(self):
        self.assertEqual(csvparse.parse_csv("abc"), [["abc"]])

    def test_lf_records(self):
        self.assertEqual(csvparse.parse_csv("a\nb\n"), [["a"], ["b"]])

    def test_crlf_records(self):
        self.assertEqual(csvparse.parse_csv("a\r\nb\r\nc\r\n"), [["a"], ["b"], ["c"]])

    def test_single_trailing_break_no_extra(self):
        self.assertEqual(csvparse.parse_csv("a\nb"), [["a"], ["b"]])
        self.assertEqual(csvparse.parse_csv("a\nb\n"), [["a"], ["b"]])

    def test_lone_cr_ends_record(self):
        self.assertEqual(csvparse.parse_csv("a\rb"), [["a"], ["b"]])

    def test_empty_line_middle(self):
        self.assertEqual(csvparse.parse_csv("a\n\nb"), [["a"], [""], ["b"]])

    def test_single_newline_is_empty_record(self):
        self.assertEqual(csvparse.parse_csv("\n"), [[""]])

    def test_double_trailing_newlines(self):
        self.assertEqual(csvparse.parse_csv("a\n\n"), [["a"], [""]])

    def test_delimiter_only(self):
        self.assertEqual(csvparse.parse_csv(",,"), [["", "", ""]])

    def test_quoted_delimiter(self):
        self.assertEqual(csvparse.parse_csv('"a,b",c'), [["a,b", "c"]])

    def test_escaped_quote(self):
        self.assertEqual(csvparse.parse_csv('"a""b"'), [['a"b']])

    def test_empty_quoted(self):
        self.assertEqual(csvparse.parse_csv('""'), [[""]])

    def test_quoted_newline(self):
        self.assertEqual(csvparse.parse_csv('"a\nb"'), [["a\nb"]])

    def test_quoted_crlf(self):
        self.assertEqual(csvparse.parse_csv('"a\r\nb"'), [["a\r\nb"]])

    def test_quote_then_break(self):
        self.assertEqual(csvparse.parse_csv('"x"\ny'), [["x"], ["y"]])

    def test_quote_then_eof(self):
        self.assertEqual(csvparse.parse_csv('"x"'), [["x"]])

    def test_unquoted_quote_is_literal(self):
        self.assertEqual(csvparse.parse_csv('ab"c'), [['ab"c']])

    def test_multiple_unquoted_quotes(self):
        self.assertEqual(csvparse.parse_csv('a"b"c'), [['a"b"c']])

    def test_unterminated_quote_raises(self):
        with self.assertRaises(ValueError):
            csvparse.parse_csv('"abc')

    def test_unterminated_quote_with_break_raises(self):
        with self.assertRaises(ValueError):
            csvparse.parse_csv('"a\nb')

    def test_char_after_quote_raises(self):
        with self.assertRaises(ValueError):
            csvparse.parse_csv('"a"b')

    def test_space_after_quote_raises(self):
        with self.assertRaises(ValueError):
            csvparse.parse_csv('"a" b')

    def test_custom_delimiter(self):
        self.assertEqual(csvparse.parse_csv("a;b;c", delimiter=";"), [["a", "b", "c"]])


class ToCsvTests(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(csvparse.to_csv([["a", "b"], ["c", "d"]]), "a,b\r\nc,d\r\n")

    def test_empty_rows(self):
        self.assertEqual(csvparse.to_csv([]), "")

    def test_empty_string_field(self):
        self.assertEqual(csvparse.to_csv([[""]]), "\r\n")

    def test_quoting_delimiter(self):
        self.assertEqual(csvparse.to_csv([["a,b"]]), '"a,b"\r\n')

    def test_quoting_quote(self):
        self.assertEqual(csvparse.to_csv([['a"b']]), '"a""b"\r\n')

    def test_quoting_newline(self):
        self.assertEqual(csvparse.to_csv([["a\nb"]]), '"a\nb"\r\n')

    def test_quoting_cr(self):
        self.assertEqual(csvparse.to_csv([["a\rb"]]), '"a\rb"\r\n')

    def test_trailing_break_present(self):
        self.assertTrue(csvparse.to_csv([["a"]]).endswith("\r\n"))

    def test_custom_delimiter(self):
        self.assertEqual(csvparse.to_csv([["a", "b"]], delimiter=";"), "a;b\r\n")


class RoundTripTests(unittest.TestCase):
    def test_roundtrip(self):
        samples = [
            [["a", "b"], ["c", "d"]],
            [[""]],
            [["a", ""], ["", "b"]],
            [["a,b"], ["c\"d"], ["e\nf"], ["g\rh"]],
            [["", "", ""]],
            [["just one"]],
            [["x""y", "z"]],
        ]
        for rows in samples:
            self.assertEqual(csvparse.parse_csv(csvparse.to_csv(rows)), rows)

    def test_randomish_roundtrip(self):
        fields = ["", "a", "a,b", 'a"b', "a\nb", "a\rb", "plain", '""']
        import random
        rng = random.Random(1234)
        for _ in range(2000):
            rows = []
            for _ in range(rng.randint(0, 4)):
                rows.append([rng.choice(fields) for _ in range(rng.randint(1, 3))])
            self.assertEqual(csvparse.parse_csv(csvparse.to_csv(rows)), rows)


if __name__ == "__main__":
    unittest.main()