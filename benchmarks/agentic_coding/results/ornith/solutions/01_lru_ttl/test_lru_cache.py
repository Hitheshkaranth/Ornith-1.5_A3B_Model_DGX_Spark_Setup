import unittest

from lru_cache import LRUCache


class TestLRUCache(unittest.TestCase):
    def test_capacity_validation(self):
        with self.assertRaises(ValueError):
            LRUCache(0)
        with self.assertRaises(ValueError):
            LRUCache(-1)

    def test_basic_put_get(self):
        c = LRUCache(2)
        c.put("a", 1)
        c.put("b", 2)
        self.assertEqual(c.get("a"), 1)
        self.assertEqual(c.get("b"), 2)

    def test_eviction_lru(self):
        c = LRUCache(2)
        c.put("a", 1)
        c.put("b", 2)
        c.get("a")  # a is now most-recent
        c.put("c", 3)  # evicts b
        self.assertIsNone(c.get("b"))
        self.assertEqual(c.get("a"), 1)
        self.assertEqual(c.get("c"), 3)

    def test_update_refreshes_recency_and_ttl(self):
        t = [0.0]
        c = LRUCache(2, ttl=1.0, clock=lambda: t[0])
        c.put("a", 1)
        t[0] = 0.5
        c.put("a", 10)  # refresh
        t[0] = 1.5
        self.assertEqual(c.get("a"), 10)  # still fresh

    def test_expiry(self):
        t = [0.0]
        c = LRUCache(1, ttl=1.0, clock=lambda: t[0])
        c.put("a", 1)
        t[0] = 1.0
        self.assertIsNone(c.get("a"))
        self.assertNotIn("a", c)
        self.assertEqual(len(c), 0)
        self.assertEqual(c.keys(), [])

    def test_expiry_boundary(self):
        t = [0.0]
        c = LRUCache(1, ttl=1.0, clock=lambda: t[0])
        c.put("a", 1)
        t[0] = 0.999
        self.assertIn("a", c)
        self.assertEqual(c.get("a"), 1)
        t[0] = 1.0
        self.assertNotIn("a", c)

    def test_purge_expired_before_eviction(self):
        t = [0.0]
        c = LRUCache(2, ttl=1.0, clock=lambda: t[0])
        c.put("a", 1)
        c.put("b", 2)
        t[0] = 1.0  # both expire
        c.put("c", 3)  # purge expired, then insert into empty cache
        self.assertIsNone(c.get("a"))
        self.assertIsNone(c.get("b"))
        self.assertEqual(c.get("c"), 3)

    def test_keys_order(self):
        c = LRUCache(3)
        c.put("a", 1)
        c.put("b", 2)
        c.put("c", 3)
        self.assertEqual(c.keys(), ["a", "b", "c"])
        c.get("a")  # a moves to most-recent
        self.assertEqual(c.keys(), ["b", "c", "a"])

    def test_contains_does_not_change_recency(self):
        c = LRUCache(2)
        c.put("a", 1)
        c.put("b", 2)
        _ = "a" in c
        c.put("c", 3)  # should evict a (still least recent)
        self.assertIsNone(c.get("a"))
        self.assertEqual(c.get("b"), 2)

    def test_never_expire(self):
        c = LRUCache(1)
        c.put("a", 1)
        c.put("b", 2)  # evicts a
        self.assertIsNone(c.get("a"))

    def test_default_value(self):
        c = LRUCache(1)
        self.assertEqual(c.get("missing", "fallback"), "fallback")
        self.assertIsNone(c.get("missing"))

    def test_len(self):
        t = [0.0]
        c = LRUCache(3, ttl=1.0, clock=lambda: t[0])
        c.put("a", 1)
        c.put("b", 2)
        self.assertEqual(len(c), 2)
        t[0] = 1.0
        self.assertEqual(len(c), 0)


if __name__ == "__main__":
    unittest.main()