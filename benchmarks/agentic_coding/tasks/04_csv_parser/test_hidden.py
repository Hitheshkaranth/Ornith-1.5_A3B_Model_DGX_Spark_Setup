import unittest, pathlib, random
from csvparse import parse_csv, to_csv


class T(unittest.TestCase):
    def test_simple(self): self.assertEqual(parse_csv("a,b,c\n1,2,3\n"), [['a', 'b', 'c'], ['1', '2', '3']])
    def test_no_trailing_newline(self): self.assertEqual(parse_csv("a,b\nc,d"), [['a', 'b'], ['c', 'd']])
    def test_crlf(self): self.assertEqual(parse_csv("a,b\r\nc,d\r\n"), [['a', 'b'], ['c', 'd']])
    def test_empty(self): self.assertEqual(parse_csv(""), [])
    def test_empty_fields(self): self.assertEqual(parse_csv(",a,,\n"), [['', 'a', '', '']])
    def test_quoted(self): self.assertEqual(parse_csv('"a,b",c\n'), [['a,b', 'c']])
    def test_escaped_quote(self): self.assertEqual(parse_csv('"he said ""hi""",x'), [['he said "hi"', 'x']])
    def test_newline_in_quotes(self): self.assertEqual(parse_csv('"line1\nline2",b\r\nc,d'), [['line1\nline2', 'b'], ['c', 'd']])
    def test_empty_quoted(self): self.assertEqual(parse_csv('"",a'), [['', 'a']])
    def test_blank_line(self): self.assertEqual(parse_csv("a\n\nb\n"), [['a'], [''], ['b']])
    def test_literal_quote_unquoted(self): self.assertEqual(parse_csv('ab"c,d'), [['ab"c', 'd']])
    def test_delimiter(self): self.assertEqual(parse_csv('a;"b;c";d', delimiter=';'), [['a', 'b;c', 'd']])

    def test_unterminated(self):
        with self.assertRaises(ValueError): parse_csv('"abc,d\n')

    def test_garbage_after_quote(self):
        with self.assertRaises(ValueError): parse_csv('"abc"x,d')

    def test_to_csv(self): self.assertEqual(to_csv([['a', 'b,c'], ['q"x', '']]), 'a,"b,c"\r\n"q""x",\r\n')

    def test_roundtrip(self):
        rnd = random.Random(7); alphabet = 'ab,"\n\r ;x'
        for _ in range(300):
            rows = [[''.join(rnd.choice(alphabet) for _ in range(rnd.randint(0, 6))) for _ in range(rnd.randint(1, 4))]
                    for _ in range(rnd.randint(1, 4))]
            self.assertEqual(parse_csv(to_csv(rows)), rows)

    def test_no_csv_module(self):
        src = pathlib.Path(__import__('csvparse').__file__).read_text(encoding="utf-8")
        self.assertNotIn('import csv', src); self.assertNotIn('from csv', src)
