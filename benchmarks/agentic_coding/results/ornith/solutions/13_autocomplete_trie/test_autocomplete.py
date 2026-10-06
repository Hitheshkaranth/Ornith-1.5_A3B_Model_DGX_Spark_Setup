import random
import time
import unittest

from autocomplete import Autocomplete


class TestAutocomplete(unittest.TestCase):
    def test_add_and_len_and_contains(self):
        ac = Autocomplete()
        self.assertEqual(len(ac), 0)
        ac.add("apple")
        ac.add("banana")
        self.assertEqual(len(ac), 2)
        self.assertIn("apple", ac)
        self.assertIn("APPLE", ac)
        self.assertNotIn("cherry", ac)

    def test_case_insensitive_return_lowercased(self):
        ac = Autocomplete()
        ac.add("Apple")
        ac.add("Banana")
        self.assertEqual(ac.suggest("A"), ["apple"])
        self.assertEqual(ac.suggest("b"), ["banana"])

    def test_weight_accumulates(self):
        ac = Autocomplete()
        ac.add("apple", 2)
        ac.add("apple", 3)
        self.assertEqual(ac.weight("apple"), 5)
        self.assertEqual(ac.weight("APPLE"), 5)

    def test_weight_default_and_absent(self):
        ac = Autocomplete()
        ac.add("x")
        self.assertEqual(ac.weight("x"), 1)
        self.assertEqual(ac.weight("nope"), 0)

    def test_remove(self):
        ac = Autocomplete()
        ac.add("apple", 3)
        self.assertTrue(ac.remove("apple"))
        self.assertEqual(ac.weight("apple"), 0)
        self.assertNotIn("apple", ac)
        self.assertEqual(len(ac), 0)
        self.assertFalse(ac.remove("apple"))

    def test_remove_partial_prefix_preserved(self):
        ac = Autocomplete()
        ac.add("ab", 1)
        ac.add("abc", 1)
        self.assertTrue(ac.remove("abc"))
        self.assertIn("ab", ac)
        self.assertNotIn("abc", ac)
        self.assertEqual(ac.suggest("a"), ["ab"])

    def test_suggest_sorting_weight_then_alpha(self):
        ac = Autocomplete()
        ac.add("avocado", 5)   # weight 5
        ac.add("ant", 5)       # weight 5 (alpha-first among the fives)
        ac.add("apple", 5)     # weight 5
        ac.add("apricot", 2)   # weight 2
        ac.add("ash", 1)       # weight 1
        # weight desc, ties alphabetical asc: ant, apple, avocado, then apricot, then ash
        self.assertEqual(ac.suggest("a", k=10), ["ant", "apple", "avocado", "apricot", "ash"])

    def test_suggest_limit_k(self):
        ac = Autocomplete()
        for i in range(20):
            ac.add("w%d" % i, weight=1)
        out = ac.suggest("w", k=5)
        self.assertEqual(len(out), 5)
        self.assertEqual(out, sorted("w%d" % i for i in range(20))[:5])

    def test_suggest_empty_prefix_all_words(self):
        ac = Autocomplete()
        ac.add("delta", 1)
        ac.add("alpha", 10)
        ac.add("gamma", 1)
        self.assertEqual(ac.suggest(""), ["alpha", "delta", "gamma"])

    def test_suggest_k_non_positive(self):
        ac = Autocomplete()
        ac.add("a", 1)
        ac.add("b", 1)
        self.assertEqual(ac.suggest("a", 0), [])
        self.assertEqual(ac.suggest("a", -3), [])

    def test_repeated_suggest_stable(self):
        ac = Autocomplete()
        ac.add("apple", 3)
        ac.add("app", 1)
        ac.add("application", 2)
        for _ in range(5):
            self.assertEqual(ac.suggest("app", k=10), ["apple", "application", "app"])

    def test_remove_then_readd(self):
        ac = Autocomplete()
        ac.add("dog", 10)
        ac.remove("dog")
        ac.add("dog", 1)
        self.assertEqual(ac.weight("dog"), 1)
        self.assertEqual(ac.suggest("d", k=5), ["dog"])

    def test_invalid_inputs(self):
        ac = Autocomplete()
        with self.assertRaises(ValueError):
            ac.add("")
        with self.assertRaises(ValueError):
            ac.add(123)
        with self.assertRaises(ValueError):
            ac.add("x", 0)
        with self.assertRaises(ValueError):
            ac.add("x", -2)
        with self.assertRaises(ValueError):
            ac.add("x", 1.5)

    def test_performance(self):
        ac = Autocomplete()
        words = ["word" + str(i) for i in range(100000)]
        for i, w in enumerate(words):
            ac.add(w, weight=(i % 7) + 1)

        self.assertEqual(len(ac), 100000)

        random.seed(0)
        prefixes = ["wo"]
        for _ in range(3000):
            p = "wo" + str(random.randint(0, 9)) + str(random.randint(0, 9))
            prefixes.append(p)

        start = time.time()
        total = 0
        for p in prefixes:
            total += len(ac.suggest(p, k=5))
        elapsed = time.time() - start

        self.assertLess(elapsed, 5.0, "3000 suggest calls took %.3fs" % elapsed)
        self.assertGreater(total, 0)


if __name__ == "__main__":
    unittest.main()
