import unittest
from semver import parse, compare, satisfies

ORDER = ["1.0.0-alpha", "1.0.0-alpha.1", "1.0.0-alpha.beta", "1.0.0-beta", "1.0.0-beta.2", "1.0.0-beta.11",
         "1.0.0-rc.1", "1.0.0", "1.0.1", "1.1.0", "1.9.0", "1.10.0", "2.0.0", "10.0.0"]


class T(unittest.TestCase):
    def test_order(self):
        for i, a in enumerate(ORDER):
            self.assertEqual(compare(a, a), 0)
            for b in ORDER[i + 1:]:
                self.assertEqual(compare(a, b), -1, (a, b)); self.assertEqual(compare(b, a), 1, (b, a))

    def test_parse(self):
        self.assertEqual(parse("1.2.3-alpha.1+build.5"), (1, 2, 3, ("alpha", "1")))
        self.assertEqual(parse("1.2.3"), (1, 2, 3, ()))
        self.assertEqual(parse("0.0.0+x"), (0, 0, 0, ()))

    def test_build_ignored(self): self.assertEqual(compare("1.0.0+a", "1.0.0+b"), 0)

    def test_invalid(self):
        for bad in ["1.2", "1.2.3.4", "01.2.3", "1.02.3", "1.2.3-", "a.b.c", "1.2.3-01", "", "v1.2.3", "1.2.3-a..b", "1.2.3+"]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError): parse(bad)

    def test_caret(self):
        self.assertTrue(satisfies("1.9.9", "^1.2.3")); self.assertFalse(satisfies("2.0.0", "^1.2.3")); self.assertFalse(satisfies("1.2.2", "^1.2.3"))
        self.assertTrue(satisfies("0.2.9", "^0.2.3")); self.assertFalse(satisfies("0.3.0", "^0.2.3"))
        self.assertTrue(satisfies("0.0.3", "^0.0.3")); self.assertFalse(satisfies("0.0.4", "^0.0.3"))

    def test_tilde(self):
        self.assertTrue(satisfies("1.2.9", "~1.2.3")); self.assertFalse(satisfies("1.3.0", "~1.2.3")); self.assertFalse(satisfies("1.2.2", "~1.2.3"))

    def test_compound(self):
        self.assertTrue(satisfies("1.5.0", ">=1.2.0 <2.0.0")); self.assertFalse(satisfies("2.0.0", ">=1.2.0 <2.0.0"))
        self.assertTrue(satisfies("3.1.0", "^1.0.0 || >=3.0.0")); self.assertFalse(satisfies("2.5.0", "^1.0.0 || >=3.0.0"))
        self.assertTrue(satisfies("1.0.0", ">=1.0.0  <=1.0.0"))

    def test_exact_and_ops(self):
        self.assertTrue(satisfies("1.2.3", "1.2.3")); self.assertFalse(satisfies("1.2.3", "=1.2.4")); self.assertTrue(satisfies("1.2.3+build", "=1.2.3"))
        self.assertFalse(satisfies("1.2.3", ">1.2.3")); self.assertTrue(satisfies("1.2.3", "<=1.2.3")); self.assertTrue(satisfies("1.0.0-rc.1", "<1.0.0"))

    def test_star(self): self.assertTrue(satisfies("4.5.6", "*"))

    def test_bad_range(self):
        for r in [">=abc", "^1.2", "", "1.0.0 || ", ">= 1.0.0"]:
            with self.subTest(r=r):
                with self.assertRaises(ValueError): satisfies("1.0.0", r)
