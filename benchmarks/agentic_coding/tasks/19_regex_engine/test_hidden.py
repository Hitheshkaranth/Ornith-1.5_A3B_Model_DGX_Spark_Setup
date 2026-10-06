import unittest, random, time, pathlib
import re as pyre
from rematch import fullmatch, search


class T(unittest.TestCase):
    def test_basic(self):
        self.assertTrue(fullmatch("abc", "abc")); self.assertFalse(fullmatch("abc", "abcd")); self.assertTrue(fullmatch("a.c", "axc"))
        self.assertTrue(fullmatch("ab*c", "ac")); self.assertTrue(fullmatch("ab+c", "abbbc")); self.assertFalse(fullmatch("ab+c", "ac"))
        self.assertTrue(fullmatch("colou?r", "color")); self.assertTrue(fullmatch("", ""))

    def test_classes(self):
        self.assertTrue(fullmatch("[a-c]+", "abcabc")); self.assertFalse(fullmatch("[a-c]+", "abd"))
        self.assertTrue(fullmatch("[^0-9]*", "abc")); self.assertFalse(fullmatch("[^0-9]*", "ab1"))
        self.assertTrue(fullmatch("[a-z0-9_]+", "var_1")); self.assertTrue(fullmatch(r"[\]x]+", "]x]")); self.assertTrue(fullmatch(r"[\-a]", "-"))

    def test_escapes(self):
        self.assertTrue(fullmatch(r"a\.b", "a.b")); self.assertFalse(fullmatch(r"a\.b", "axb")); self.assertTrue(fullmatch(r"\*+", "***"))
        self.assertTrue(fullmatch(r"\[x\]", "[x]")); self.assertTrue(fullmatch(r"a\\b", "a\\b"))

    def test_search_anchors(self):
        self.assertTrue(search("b+c", "aabbcd")); self.assertFalse(search("^b", "ab")); self.assertTrue(search("^a", "ab"))
        self.assertTrue(search("b$", "ab")); self.assertFalse(search("a$", "ab")); self.assertTrue(search("^ab$", "ab"))
        self.assertTrue(search("x*", "")); self.assertTrue(search(r"\$", "a$b")); self.assertTrue(search("", "abc"))

    def test_invalid(self):
        for p in ["*a", "+", "a**", "a+?", "a?*", "[abc", "[z-a]", "a\\", "[]"]:
            with self.subTest(p=p):
                with self.assertRaises(ValueError): fullmatch(p, "a")

    def test_random_vs_re(self):
        rnd = random.Random(9)
        atoms = ['a', 'b', '.', '[ab]', '[^a]', '[a-b]', 'c']
        for _ in range(1500):
            p = ''.join(rnd.choice(atoms) + rnd.choice(['', '', '*', '+', '?']) for _ in range(rnd.randint(1, 5)))
            for _ in range(4):
                t = ''.join(rnd.choice('abc') for _ in range(rnd.randint(0, 8)))
                self.assertEqual(fullmatch(p, t), pyre.fullmatch(p, t) is not None, (p, t))
                self.assertEqual(search(p, t), pyre.search(p, t) is not None, (p, t))

    def test_pathological(self):
        t = time.perf_counter()
        self.assertFalse(fullmatch("a*a*a*a*a*a*a*a*b", "a" * 40))
        self.assertFalse(search("a*a*a*a*a*a*b", "a" * 60))
        self.assertTrue(fullmatch(".*.*.*x", "y" * 200 + "x"))
        self.assertLess(time.perf_counter() - t, 3.0)

    def test_no_re(self):
        src = pathlib.Path(__import__('rematch').__file__).read_text(encoding="utf-8")
        self.assertNotIn("import re\n", src + "\n"); self.assertNotIn("from re ", src); self.assertNotIn("import re,", src)
