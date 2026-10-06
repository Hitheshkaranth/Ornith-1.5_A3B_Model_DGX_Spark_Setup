import unittest, random, time
from editdist import levenshtein, alignment, osa_distance, closest


def ref_lev(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def ref_osa(a, b):
    n, m = len(a), len(b); D = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1): D[i][0] = i
    for j in range(m + 1): D[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            D[i][j] = min(D[i - 1][j] + 1, D[i][j - 1] + 1, D[i - 1][j - 1] + (a[i - 1] != b[j - 1]))
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                D[i][j] = min(D[i][j], D[i - 2][j - 2] + 1)
    return D[n][m]


def apply(tc, a, ops):
    i = 0; out = []
    for op in ops:
        op = tuple(op)
        if op[0] == 'keep':
            tc.assertEqual(a[i], op[1]); out.append(op[1]); i += 1
        elif op[0] == 'sub':
            tc.assertEqual(a[i], op[1]); out.append(op[2]); i += 1
        elif op[0] == 'ins':
            out.append(op[1])
        elif op[0] == 'del':
            tc.assertEqual(a[i], op[1]); i += 1
        else:
            tc.fail("bad op %r" % (op,))
    tc.assertEqual(i, len(a)); return ''.join(out)


class T(unittest.TestCase):
    def test_known(self):
        self.assertEqual(levenshtein("kitten", "sitting"), 3); self.assertEqual(levenshtein("", "abc"), 3)
        self.assertEqual(levenshtein("flaw", "lawn"), 2); self.assertEqual(levenshtein("same", "same"), 0)
        self.assertEqual(levenshtein("ab", "ba"), 2)

    def test_osa_known(self):
        self.assertEqual(osa_distance("ca", "abc"), 3); self.assertEqual(osa_distance("ab", "ba"), 1)
        self.assertEqual(osa_distance("", ""), 0); self.assertEqual(osa_distance("abcdef", "abdcef"), 1)

    def test_random(self):
        rnd = random.Random(5)
        for _ in range(400):
            a = ''.join(rnd.choice('abc') for _ in range(rnd.randint(0, 9)))
            b = ''.join(rnd.choice('abc') for _ in range(rnd.randint(0, 9)))
            d = ref_lev(a, b)
            self.assertEqual(levenshtein(a, b), d, (a, b))
            self.assertEqual(osa_distance(a, b), ref_osa(a, b), (a, b))
            ops = alignment(a, b)
            self.assertEqual(apply(self, a, ops), b, (a, b))
            self.assertEqual(sum(1 for o in ops if o[0] != 'keep'), d, (a, b, ops))

    def test_alignment_example(self):
        ops = alignment("kitten", "sitting"); self.assertEqual(apply(self, "kitten", ops), "sitting")
        self.assertEqual(sum(o[0] != 'keep' for o in ops), 3)

    def test_closest(self):
        c = ["apple", "apply", "ample", "maple", "apples"]
        self.assertEqual(closest("appl", c), ["apple", "apply"])
        self.assertEqual(closest("zzzzzz", c, max_distance=2), [])
        self.assertEqual(closest("x", []), [])

    def test_speed(self):
        rnd = random.Random(1)
        a = ''.join(rnd.choice('abcd') for _ in range(1000)); b = ''.join(rnd.choice('abcd') for _ in range(1000))
        t = time.perf_counter(); d = levenshtein(a, b); self.assertLess(time.perf_counter() - t, 8)
        self.assertEqual(d, ref_lev(a, b))
