import unittest, random, time
from autocomplete import Autocomplete


class T(unittest.TestCase):
    def test_basic(self):
        a = Autocomplete()
        for w, x in [("apple", 5), ("app", 3), ("application", 5), ("apt", 1), ("banana", 9)]: a.add(w, x)
        self.assertEqual(a.suggest("ap"), ["apple", "application", "app", "apt"])
        self.assertEqual(a.suggest("ap", k=2), ["apple", "application"])
        self.assertEqual(a.suggest("b"), ["banana"]); self.assertEqual(a.suggest("z"), [])

    def test_case_insensitive(self):
        a = Autocomplete(); a.add("Hello", 2); a.add("help")
        self.assertEqual(a.suggest("HE"), ["hello", "help"]); self.assertIn("HELLO", a); self.assertEqual(a.weight("hElLo"), 2)

    def test_accumulate(self):
        a = Autocomplete(); a.add("x", 2); a.add("X", 3); self.assertEqual(a.weight("x"), 5); self.assertEqual(len(a), 1)

    def test_remove(self):
        a = Autocomplete(); a.add("car"); a.add("cart"); self.assertTrue(a.remove("car")); self.assertFalse(a.remove("car"))
        self.assertEqual(a.suggest("ca"), ["cart"]); self.assertNotIn("car", a); self.assertEqual(len(a), 1); self.assertEqual(a.weight("car"), 0)

    def test_empty_prefix_and_k(self):
        a = Autocomplete(); a.add("b", 1); a.add("a", 1); a.add("c", 2)
        self.assertEqual(a.suggest(""), ["c", "a", "b"]); self.assertEqual(a.suggest("", k=0), [])

    def test_validation(self):
        a = Autocomplete()
        for args in [("",), ("x", 0), ("x", -1), ("x", 1.5), (None,)]:
            with self.assertRaises(ValueError): a.add(*args)

    def test_performance(self):
        rnd = random.Random(2); a = Autocomplete(); words = set()
        while len(words) < 100000:
            words.add(''.join(rnd.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(rnd.randint(5, 10))))
        words = sorted(words)
        for w in words: a.add(w, rnd.randint(1, 100))
        qs = [w[:rnd.randint(3, 4)] for w in rnd.sample(words, 4000)]
        t = time.perf_counter()
        for q in qs: a.suggest(q, 5)
        self.assertLess(time.perf_counter() - t, 6.0)
        q = qs[0]; exp = sorted([w for w in words if w.startswith(q)], key=lambda w: (-a.weight(w), w))[:5]
        self.assertEqual(a.suggest(q, 5), exp)
