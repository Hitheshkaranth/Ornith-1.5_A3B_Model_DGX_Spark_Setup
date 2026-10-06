import unittest

from semver import parse, compare, satisfies


class TestParse(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(parse("1.2.3"), (1, 2, 3, ()))
        self.assertEqual(parse("0.0.0"), (0, 0, 0, ()))

    def test_metadata_dropped(self):
        self.assertEqual(parse("1.2.3+build"), (1, 2, 3, ()))
        self.assertEqual(parse("1.2.3-alpha.1+build.5"), (1, 2, 3, ("alpha", "1")))
        self.assertEqual(parse("1.0.0+20130313144700"), (1, 0, 0, ()))

    def test_prerelease_ids(self):
        self.assertEqual(parse("1.0.0-alpha"), (1, 0, 0, ("alpha",)))
        self.assertEqual(parse("1.0.0-alpha.1"), (1, 0, 0, ("alpha", "1")))
        self.assertEqual(parse("1.0.0-0.3.7"), (1, 0, 0, ("0", "3", "7")))
        self.assertEqual(parse("1.0.0-alpha.1.beta-2"), (1, 0, 0, ("alpha", "1", "beta-2")))

    def test_invalid(self):
        for bad in [
            "1.2", "1", "1.2.3.4", "v1.2.3", "01.2.3", "1.02.3",
            "1.2.03", "1.2.3-alpha..1", "1.2.3-01",
            "-1.2.3", "1.2.3-", "+1.2.3", "1.2.3 ", " 1.2.3",
            "1.2.3-..", "00.0.0", "1.2.3-00",
        ]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    parse(bad)


class TestCompare(unittest.TestCase):
    def test_core(self):
        self.assertEqual(compare("1.0.0", "2.0.0"), -1)
        self.assertEqual(compare("2.0.0", "1.0.0"), 1)
        self.assertEqual(compare("1.2.0", "1.1.9"), 1)
        self.assertEqual(compare("1.0.1", "1.0.0"), 1)
        self.assertEqual(compare("1.0.0", "1.0.0"), 0)

    def test_metadata_ignored(self):
        self.assertEqual(compare("1.0.0+build", "1.0.0+other"), 0)

    def test_prerelease_precedence(self):
        self.assertEqual(compare("1.0.0-alpha", "1.0.0"), -1)
        self.assertEqual(compare("1.0.0", "1.0.0-alpha"), 1)
        self.assertEqual(compare("1.0.0-alpha", "1.0.0-alpha.1"), -1)
        self.assertEqual(compare("1.0.0-alpha.1", "1.0.0-alpha.beta"), -1)
        self.assertEqual(compare("1.0.0-alpha.beta", "1.0.0-beta"), -1)
        self.assertEqual(compare("1.0.0-beta", "1.0.0-beta.2"), -1)
        self.assertEqual(compare("1.0.0-beta.2", "1.0.0-beta.11"), -1)
        self.assertEqual(compare("1.0.0-beta.11", "1.0.0-rc.1"), -1)
        self.assertEqual(compare("1.0.0-rc.1", "1.0.0"), -1)

    def test_numeric_vs_alpha(self):
        self.assertEqual(compare("1.0.0-1", "1.0.0-alpha"), -1)


class TestSatisfies(unittest.TestCase):
    def test_exact_bare(self):
        self.assertTrue(satisfies("1.2.3", "1.2.3"))
        self.assertFalse(satisfies("1.2.4", "1.2.3"))
        self.assertTrue(satisfies("1.2.3", "=1.2.3"))

    def test_relational(self):
        self.assertTrue(satisfies("1.2.3", ">=1.2.0"))
        self.assertFalse(satisfies("1.1.9", ">=1.2.0"))
        self.assertTrue(satisfies("1.2.4", ">1.2.3"))
        self.assertFalse(satisfies("1.2.3", ">1.2.3"))
        self.assertTrue(satisfies("1.2.3", "<=1.2.3"))
        self.assertTrue(satisfies("1.2.2", "<1.2.3"))

    def test_star(self):
        self.assertTrue(satisfies("9.9.9", "*"))

    def test_caret(self):
        self.assertTrue(satisfies("1.2.3", "^1.2.3"))
        self.assertTrue(satisfies("1.9.9", "^1.2.3"))
        self.assertFalse(satisfies("2.0.0", "^1.2.3"))
        self.assertFalse(satisfies("1.2.2", "^1.2.3"))
        self.assertTrue(satisfies("0.2.9", "^0.2.3"))
        self.assertFalse(satisfies("0.3.0", "^0.2.3"))
        self.assertTrue(satisfies("0.0.3", "^0.0.3"))
        self.assertFalse(satisfies("0.0.4", "^0.0.3"))

    def test_tilde(self):
        self.assertTrue(satisfies("1.2.3", "~1.2.3"))
        self.assertTrue(satisfies("1.2.9", "~1.2.3"))
        self.assertFalse(satisfies("1.3.0", "~1.2.3"))

    def test_combined(self):
        self.assertTrue(satisfies("1.2.5", ">=1.2.0 <1.3.0"))
        self.assertFalse(satisfies("1.3.0", ">=1.2.0 <1.3.0"))

    def test_alternatives(self):
        self.assertTrue(satisfies("1.5.0", ">=3.0.0 || <2.0.0"))
        self.assertFalse(satisfies("2.5.0", ">=3.0.0 || <2.0.0"))

    def test_metadata_in_version_arg(self):
        self.assertTrue(satisfies("1.2.3+build", ">=1.2.3"))


class TestMalformedRange(unittest.TestCase):
    def test_empty(self):
        with self.assertRaises(ValueError):
            satisfies("1.2.3", "")
        with self.assertRaises(ValueError):
            satisfies("1.2.3", "   ")

    def test_empty_alternative(self):
        with self.assertRaises(ValueError):
            satisfies("1.2.3", ">=1.0.0 ||")
        with self.assertRaises(ValueError):
            satisfies("1.2.3", "|| >=1.0.0")

    def test_bad_version(self):
        with self.assertRaises(ValueError):
            satisfies("1.2.3", ">=1.2")
        with self.assertRaises(ValueError):
            satisfies("1.2.3", "v1.2.3")
        with self.assertRaises(ValueError):
            satisfies("1.2.3", "^1.2")

    def test_bad_version_arg(self):
        with self.assertRaises(ValueError):
            satisfies("not a version", ">=1.0.0")


if __name__ == "__main__":
    unittest.main(verbosity=2)