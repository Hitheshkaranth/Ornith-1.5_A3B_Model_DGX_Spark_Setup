import unittest
from ratelimit import TokenBucket, KeyedLimiter


class Clock:
    def __init__(self): self.t = 0.0
    def __call__(self): return self.t


class T(unittest.TestCase):
    def test_starts_full(self):
        clk = Clock(); b = TokenBucket(1, 5, clk)
        self.assertEqual([b.allow() for _ in range(6)], [True] * 5 + [False])

    def test_refill(self):
        clk = Clock(); b = TokenBucket(1, 5, clk)
        for _ in range(5): b.allow()
        clk.t = 2.0
        self.assertEqual([b.allow() for _ in range(3)], [True, True, False])

    def test_cap(self):
        clk = Clock(); b = TokenBucket(1, 5, clk); b.allow(5); clk.t = 1000
        self.assertAlmostEqual(b.tokens, 5)

    def test_fractional(self):
        clk = Clock(); b = TokenBucket(2, 1, clk); self.assertTrue(b.allow())
        clk.t = 0.25; self.assertFalse(b.allow()); clk.t = 0.5; self.assertTrue(b.allow())

    def test_fail_consumes_nothing(self):
        clk = Clock(); b = TokenBucket(1, 5, clk); self.assertTrue(b.allow(4)); self.assertFalse(b.allow(3)); self.assertTrue(b.allow(1))

    def test_wait_time(self):
        clk = Clock(); b = TokenBucket(2, 4, clk); b.allow(4)
        self.assertAlmostEqual(b.wait_time(1), 0.5); self.assertAlmostEqual(b.wait_time(4), 2.0)
        clk.t = 0.5; self.assertAlmostEqual(b.wait_time(1), 0.0); self.assertTrue(b.allow(1))

    def test_wait_time_no_consume(self):
        clk = Clock(); b = TokenBucket(1, 3, clk); b.wait_time(2); b.wait_time(3); self.assertTrue(b.allow(3))

    def test_errors(self):
        clk = Clock(); b = TokenBucket(1, 5, clk)
        for bad in (6, 0, -1):
            with self.assertRaises(ValueError): b.allow(bad)
            with self.assertRaises(ValueError): b.wait_time(bad)
        with self.assertRaises(ValueError): TokenBucket(0, 5, clk)
        with self.assertRaises(ValueError): TokenBucket(1, 0, clk)

    def test_tokens_property(self):
        clk = Clock(); b = TokenBucket(1, 5, clk); b.allow(2); self.assertAlmostEqual(b.tokens, 3.0)

    def test_keyed(self):
        clk = Clock(); k = KeyedLimiter(1, 2, clk)
        self.assertEqual([k.allow('a') for _ in range(3)], [True, True, False])
        self.assertTrue(k.allow('b')); clk.t = 1.0; self.assertTrue(k.allow('a'))
