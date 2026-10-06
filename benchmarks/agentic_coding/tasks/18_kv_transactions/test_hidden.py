import unittest, time
from kvstore import KVStore, NoTransaction


class T(unittest.TestCase):
    def test_basic(self):
        s = KVStore(); s.set('a', 10); self.assertEqual(s.get('a'), 10); self.assertIsNone(s.get('b'))
        self.assertTrue(s.delete('a')); self.assertFalse(s.delete('a')); self.assertIsNone(s.get('a'))

    def test_count(self):
        s = KVStore(); s.set('a', 10); s.set('b', 10); s.set('c', 20)
        self.assertEqual(s.count(10), 2); s.set('a', 20); self.assertEqual(s.count(10), 1); self.assertEqual(s.count(20), 2)
        s.delete('c'); self.assertEqual(s.count(20), 1); self.assertEqual(s.count(99), 0)

    def test_rollback(self):
        s = KVStore(); s.set('a', 1); s.begin(); s.set('a', 2); s.set('b', 3); s.delete('a'); s.rollback()
        self.assertEqual(s.get('a'), 1); self.assertIsNone(s.get('b')); self.assertEqual(s.count(1), 1); self.assertEqual(s.count(3), 0)

    def test_nested(self):
        s = KVStore(); s.begin(); s.set('a', 10); s.begin(); s.set('a', 20); s.set('a', 30)
        self.assertEqual(s.get('a'), 30); s.rollback(); self.assertEqual(s.get('a'), 10); s.rollback(); self.assertIsNone(s.get('a'))
        with self.assertRaises(NoTransaction): s.rollback()

    def test_commit_all(self):
        s = KVStore(); s.begin(); s.set('a', 1); s.begin(); s.set('b', 2); s.commit()
        self.assertEqual((s.get('a'), s.get('b')), (1, 2))
        with self.assertRaises(NoTransaction): s.rollback()
        with self.assertRaises(NoTransaction): s.commit()

    def test_delete_in_tx(self):
        s = KVStore(); s.set('x', 'v'); s.begin(); s.delete('x'); self.assertEqual(s.count('v'), 0); s.rollback()
        self.assertEqual(s.get('x'), 'v'); self.assertEqual(s.count('v'), 1)

    def test_nested_count(self):
        s = KVStore(); s.set('a', 1); s.begin(); s.set('b', 1); s.begin(); s.set('a', 2)
        self.assertEqual(s.count(1), 1); s.rollback(); self.assertEqual(s.count(1), 2); s.rollback(); self.assertEqual(s.count(1), 1)

    def test_count_performance(self):
        s = KVStore()
        for i in range(200000): s.set(i, i % 3)
        t = time.perf_counter()
        for i in range(20000): s.count(i % 3)
        self.assertLess(time.perf_counter() - t, 1.0)
        self.assertEqual(s.count(0), 66667)
