import random
import string
import time
import unittest

from editdist import levenshtein, alignment, osa_distance, closest, _apply


def ref_levenshtein(a, b):
    n, m = len(a), len(b)
    dp = list(range(m + 1))
    for i in range(1, n + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, m + 1):
            temp = dp[j]
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + cost)
            prev = temp
    return dp[m]


def ref_osas(a, b):
    """Textbook 2-matrix restricted Damerau-Levenshtein reference."""
    n, m = len(a), len(b)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + cost)
    return d[n][m]


class TestLevenshtein(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(levenshtein('', ''), 0)
        self.assertEqual(levenshtein('', 'abc'), 3)
        self.assertEqual(levenshtein('abc', ''), 3)
        self.assertEqual(levenshtein('abc', 'abc'), 0)
        self.assertEqual(levenshtein('kitten', 'sitting'), 3)
        self.assertEqual(levenshtein('flaw', 'lawn'), 2)
        self.assertEqual(levenshtein('ab', 'ba'), 2)

    def test_symmetry(self):
        for a, b in [('kitten', 'sitting'), ('ca', 'abc'), ('abc', 'xyz')]:
            self.assertEqual(levenshtein(a, b), levenshtein(b, a))


class TestAlignment(unittest.TestCase):
    def test_transform_and_count(self):
        for a, b in [('kitten', 'sitting'), ('ca', 'abc'), ('', 'abc'),
                     ('abc', ''), ('same', 'same'), ('abc', 'abc')]:
            ops = alignment(a, b)
            self.assertEqual(_apply(ops), b)
            self.assertEqual(
                sum(1 for op in ops if op[0] != 'keep'),
                levenshtein(a, b),
            )

    def test_ops_valid(self):
        ops = alignment('kitten', 'sitting')
        for op in ops:
            self.assertIn(op[0], ('keep', 'sub', 'ins', 'del'))


class TestOSA(unittest.TestCase):
    def test_given(self):
        self.assertEqual(osa_distance('ca', 'abc'), 3)
        self.assertEqual(osa_distance('ab', 'ba'), 1)

    def test_properties(self):
        self.assertEqual(osa_distance('', ''), 0)
        self.assertEqual(osa_distance('abc', 'abc'), 0)
        self.assertEqual(osa_distance('ab', 'ba'), 1)
        self.assertEqual(osa_distance('da', 'ad'), 1)

    def test_not_greater_than_levenshtein(self):
        # A transposition can only reduce the cost, so osa <= levenshtein.
        for a, b in [('kitten', 'sitting'), ('cat', 'car'), ('ab', 'ba'),
                     ('abc', 'acb'), ('ca', 'abc')]:
            self.assertLessEqual(osa_distance(a, b), levenshtein(a, b))


class TestClosest(unittest.TestCase):
    def test_minimal_order(self):
        self.assertEqual(
            closest('cat', ['car', 'cot', 'dog', 'bat']),
            ['car', 'cot', 'bat'],
        )

    def test_minimal_with_duplicate_min(self):
        self.assertEqual(closest('cat', ['abc', 'xyz']), ['abc', 'xyz'])

    def test_max_distance(self):
        self.assertEqual(
            closest('cat', ['car', 'cot', 'dog', 'bat'], max_distance=2),
            ['car', 'cot', 'bat'],
        )
        self.assertEqual(
            closest('cat', ['car', 'cot', 'dog', 'bat'], max_distance=1),
            ['car', 'cot', 'bat'],
        )
        self.assertEqual(
            closest('cat', ['car', 'cot', 'dog', 'bat'], max_distance=0),
            [],
        )

    def test_exclusion_and_empty(self):
        self.assertEqual(closest('cat', ['zzzz', 'yyyy']), ['zzzz', 'yyyy'])
        self.assertEqual(
            closest('cat', ['zzzz', 'yyyy'], max_distance=1), []
        )
        self.assertEqual(closest('cat', [], max_distance=1), [])

    def test_exact_match_wins(self):
        self.assertEqual(closest('abc', ['abc', 'abd', 'xyz']), ['abc'])


def test_random_against_reference():
    rng = random.Random(1234)
    for _ in range(400):
        a = ''.join(rng.choice('abc') for _ in range(rng.randint(0, 9)))
        b = ''.join(rng.choice('abc') for _ in range(rng.randint(0, 9)))
        assert levenshtein(a, b) == ref_levenshtein(a, b)
        assert osa_distance(a, b) == ref_osas(a, b)
        ops = alignment(a, b)
        assert _apply(ops) == b
        assert sum(1 for op in ops if op[0] != 'keep') == levenshtein(a, b)


def test_performance():
    rng = random.Random(1)
    a = ''.join(rng.choice(string.ascii_lowercase) for _ in range(1000))
    b = ''.join(rng.choice(string.ascii_lowercase) for _ in range(1000))
    t0 = time.time()
    d = levenshtein(a, b)
    ops = alignment(a, b)
    o = osa_distance(a, b)
    elapsed = time.time() - t0
    assert _apply(ops) == b
    assert sum(1 for op in ops if op[0] != 'keep') == d
    print(f'\n1000-char levenshtein={d}, osa={o}, time={elapsed:.3f}s')
    assert elapsed < 10


if __name__ == '__main__':
    test_random_against_reference()
    test_performance()
    print('All standalone checks passed.')
    unittest.main(verbosity=2)