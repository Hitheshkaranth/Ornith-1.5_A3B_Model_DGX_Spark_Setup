import time
import unittest

from rematch import fullmatch, search


def expect_error(fn, *args):
    raised = False
    try:
        fn(*args)
    except ValueError:
        raised = True
    assert raised, "expected ValueError for %r" % (args,)


class TestFullmatch(unittest.TestCase):
    def test_literals(self):
        self.assertTrue(fullmatch("abc", "abc"))
        self.assertFalse(fullmatch("abc", "abd"))
        self.assertFalse(fullmatch("abc", "abcd"))
        self.assertFalse(fullmatch("ab", "abc"))
        self.assertTrue(fullmatch("", ""))
        self.assertFalse(fullmatch("", "x"))

    def test_dot(self):
        self.assertTrue(fullmatch("a.c", "abc"))
        self.assertTrue(fullmatch("a.c", "aXc"))
        self.assertFalse(fullmatch("a.c", "ac"))
        self.assertTrue(fullmatch("...", "abc"))

    def test_quantifiers(self):
        self.assertTrue(fullmatch("ab*c", "ac"))
        self.assertTrue(fullmatch("ab*c", "abc"))
        self.assertTrue(fullmatch("ab*c", "abbbbc"))
        self.assertFalse(fullmatch("ab*c", "abbc"[:-1] + "x"))
        self.assertTrue(fullmatch("ab+c", "abc"))
        self.assertTrue(fullmatch("ab+c", "abbbc"))
        self.assertFalse(fullmatch("ab+c", "ac"))
        self.assertTrue(fullmatch("ab?c", "ac"))
        self.assertTrue(fullmatch("ab?c", "abc"))
        self.assertFalse(fullmatch("ab?c", "abbc"))

    def test_classes(self):
        self.assertTrue(fullmatch("[abc]", "a"))
        self.assertTrue(fullmatch("[abc]", "c"))
        self.assertFalse(fullmatch("[abc]", "d"))
        self.assertTrue(fullmatch("[a-z]", "m"))
        self.assertTrue(fullmatch("[a-z]", "a"))
        self.assertTrue(fullmatch("[a-z]", "z"))
        self.assertFalse(fullmatch("[a-z]", "A"))
        self.assertTrue(fullmatch("[a-z0-9]", "5"))
        self.assertFalse(fullmatch("[a-z0-9]", "@"))
        self.assertTrue(fullmatch("[^abc]", "d"))
        self.assertFalse(fullmatch("[^abc]", "a"))
        self.assertFalse(fullmatch("[^a-z]", "m"))

    def test_escapes(self):
        self.assertTrue(fullmatch("a\\.c", "a.c"))
        self.assertFalse(fullmatch("a\\.c", "abc"))
        self.assertTrue(fullmatch("a\\*c", "a*c"))
        self.assertTrue(fullmatch("a\\+c", "a+c"))
        self.assertTrue(fullmatch("\\[", "["))
        self.assertTrue(fullmatch("\\]", "]"))
        self.assertTrue(fullmatch("\\\\", "\\"))
        self.assertTrue(fullmatch("\\.", "."))

    def test_class_with_escapes(self):
        self.assertTrue(fullmatch("[\\.]", "."))
        self.assertTrue(fullmatch("[a-z]+", "abcd"))
        self.assertTrue(fullmatch("[^a-z]*", "12345"))

    def test_dot_with_quantifier(self):
        self.assertTrue(fullmatch(".*", "anything at all"))
        self.assertTrue(fullmatch(".*", ""))
        self.assertTrue(fullmatch("a.*c", "abbbc"))
        self.assertTrue(fullmatch(".*c", "abbc"))

    def test_complex(self):
        self.assertTrue(fullmatch("a.*", "aaaa"))
        self.assertTrue(fullmatch(".+.", "abc"))
        self.assertTrue(fullmatch(".+.", "ab"))
        self.assertFalse(fullmatch(".+.", "a"))
        self.assertTrue(fullmatch("[a-z]*", ""))


class TestSearch(unittest.TestCase):
    def test_substring(self):
        self.assertTrue(search("bc", "abcd"))
        self.assertFalse(search("xc", "abcd"))
        self.assertTrue(search("a", "abcd"))
        self.assertTrue(search("", "anything"))
        self.assertTrue(search("xyz", "a xyz w"))

    def test_dot(self):
        self.assertTrue(search("a.c", "axcde"))
        self.assertFalse(search("a.c", "acde"))

    def test_anchors(self):
        self.assertTrue(search("^abc", "abcdef"))
        self.assertFalse(search("^xyz", "abcdef"))
        self.assertTrue(search("xyz$", "abcdxyz"))
        self.assertFalse(search("xyz$", "xyzabcd"))
        self.assertTrue(search("^x$", "x"))
        self.assertFalse(search("^x$", "xy"))
        self.assertTrue(search("^a", "abc"))
        self.assertFalse(search("^b", "abc"))

    def test_no_anchor_still_searches(self):
        self.assertTrue(search("a", "ba"))
        self.assertTrue(search("a$", "ba"))
        self.assertFalse(search("b$", "ba"))

    def test_anchors_fullmatch_no_effect(self):
        # ^ and $ are accepted in fullmatch but have no effect (fullmatch
        # already requires the entire text to match).
        self.assertTrue(fullmatch("^abc$", "abc"))
        self.assertTrue(fullmatch("^ab", "ab"))
        self.assertTrue(fullmatch("a$", "a"))
        self.assertTrue(fullmatch("ab$", "ab"))
        self.assertFalse(fullmatch("^ab", "abc"))
        self.assertFalse(fullmatch("a$", "ba"))


class TestErrors(unittest.TestCase):
    def test_quantifier_nothing_to_repeat(self):
        expect_error(fullmatch, "*a", "a")
        expect_error(fullmatch, "+", "")
        expect_error(fullmatch, "?", "")
        expect_error(fullmatch, "a*+", "aa")
        expect_error(search, "a*?+", "aa")

    def test_stacked_quantifiers(self):
        expect_error(fullmatch, "a**", "aa")
        expect_error(fullmatch, "a+?", "aa")
        expect_error(fullmatch, "a?*", "aa")
        # two independent quantifiers on separate atoms is valid:
        self.assertTrue(search(".*.*", "aa"))

    def test_unterminated_class(self):
        expect_error(fullmatch, "[abc", "abc")
        expect_error(fullmatch, "[a-z", "m")
        expect_error(fullmatch, "[", "")

    def test_reversed_range(self):
        expect_error(fullmatch, "[z-a]", "m")
        expect_error(fullmatch, "[9-0]", "5")

    def test_trailing_backslash(self):
        expect_error(fullmatch, "abc\\", "abc\\")
        expect_error(fullmatch, "\\", "")
        expect_error(fullmatch, "a\\", "a")


class TestPerformance(unittest.TestCase):
    def test_no_exponential_blowup(self):
        t0 = time.time()
        result = fullmatch("a*a*a*a*a*a*a*a*b", "a" * 40)
        elapsed = time.time() - t0
        self.assertFalse(result)
        self.assertLess(elapsed, 1.0)

    def test_longer_input(self):
        t0 = time.time()
        result = fullmatch("a*a*a*a*a*a*a*a*b", "a" * 500)
        elapsed = time.time() - t0
        self.assertFalse(result)
        self.assertLess(elapsed, 2.0)

    def test_matching_long_input_fast(self):
        t0 = time.time()
        result = fullmatch("a*a*a*a*a*a*a*a*a", "a" * 500)
        elapsed = time.time() - t0
        self.assertTrue(result)
        self.assertLess(elapsed, 2.0)

    def test_search_does_not_blow_up(self):
        t0 = time.time()
        result = search("a*.*b", "a" * 300 + "b")
        elapsed = time.time() - t0
        self.assertTrue(result)
        self.assertLess(elapsed, 2.0)


if __name__ == "__main__":
    unittest.main()