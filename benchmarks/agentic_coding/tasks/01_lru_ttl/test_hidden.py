import unittest
from lru_cache import LRUCache


class Clock:
    def __init__(self): self.t = 0.0
    def __call__(self): return self.t


class T(unittest.TestCase):
    def test_bad_capacity(self):
        with self.assertRaises(ValueError): LRUCache(0)

    def test_evicts_lru(self):
        c = LRUCache(2); c.put('a', 1); c.put('b', 2); c.put('c', 3)
        self.assertIsNone(c.get('a')); self.assertEqual(c.get('b'), 2); self.assertEqual(c.get('c'), 3)

    def test_get_refreshes(self):
        c = LRUCache(2); c.put('a', 1); c.put('b', 2); c.get('a'); c.put('c', 3)
        self.assertEqual(c.get('a'), 1); self.assertIsNone(c.get('b'))

    def test_update_existing_no_evict(self):
        c = LRUCache(2); c.put('a', 1); c.put('b', 2); c.put('a', 10)
        self.assertEqual(len(c), 2); self.assertEqual(c.get('a'), 10); self.assertEqual(c.get('b'), 2)

    def test_update_refreshes_recency(self):
        c = LRUCache(2); c.put('a', 1); c.put('b', 2); c.put('a', 5); c.put('c', 3)
        self.assertNotIn('b', c); self.assertIn('a', c)

    def test_default(self):
        self.assertEqual(LRUCache(1).get('x', 'd'), 'd')

    def test_ttl_expiry(self):
        clk = Clock(); c = LRUCache(3, ttl=10, clock=clk); c.put('a', 1); clk.t = 9.9
        self.assertEqual(c.get('a'), 1); clk.t = 10.0
        self.assertIsNone(c.get('a')); self.assertEqual(len(c), 0)

    def test_ttl_reset_on_update(self):
        clk = Clock(); c = LRUCache(3, ttl=10, clock=clk); c.put('a', 1); clk.t = 8; c.put('a', 2); clk.t = 15
        self.assertEqual(c.get('a'), 2)

    def test_len_excludes_expired(self):
        clk = Clock(); c = LRUCache(5, ttl=5, clock=clk); c.put('a', 1); clk.t = 3; c.put('b', 2); clk.t = 6
        self.assertEqual(len(c), 1); self.assertNotIn('a', c); self.assertIn('b', c)

    def test_purge_expired_before_lru_eviction(self):
        clk = Clock(); c = LRUCache(2, ttl=5, clock=clk)
        c.put('a', 1); clk.t = 4; c.put('b', 2); clk.t = 4.5; c.get('a')
        clk.t = 5.5
        c.put('c', 3)
        self.assertEqual(c.get('b'), 2); self.assertEqual(c.get('c'), 3)

    def test_contains_no_recency(self):
        c = LRUCache(2); c.put('a', 1); c.put('b', 2); self.assertIn('a', c); c.put('c', 3)
        self.assertNotIn('a', c); self.assertIn('b', c)

    def test_keys_order(self):
        c = LRUCache(3); c.put('a', 1); c.put('b', 2); c.put('c', 3); c.get('a')
        self.assertEqual(c.keys(), ['b', 'c', 'a'])

    def test_no_ttl_never_expires(self):
        clk = Clock(); c = LRUCache(2, clock=clk); c.put('a', 1); clk.t = 1e9
        self.assertEqual(c.get('a'), 1)
