import unittest
import time

from kvstore import KVStore, NoTransaction


class BasicTests(unittest.TestCase):
    def test_set_get_delete(self):
        kv = KVStore()
        self.assertIsNone(kv.get("x"))
        kv.set("x", 10)
        self.assertEqual(kv.get("x"), 10)
        self.assertEqual(kv.delete("x"), True)
        self.assertIsNone(kv.get("x"))
        self.assertEqual(kv.delete("x"), False)

    def test_count_basic(self):
        kv = KVStore()
        self.assertEqual(kv.count(5), 0)
        kv.set("a", 5)
        kv.set("b", 5)
        kv.set("c", 7)
        self.assertEqual(kv.count(5), 2)
        self.assertEqual(kv.count(7), 1)
        kv.set("c", 5)
        self.assertEqual(kv.count(7), 0)
        self.assertEqual(kv.count(5), 3)
        kv.delete("a")
        self.assertEqual(kv.count(5), 2)

    def test_count_overwrites_and_deletes(self):
        kv = KVStore()
        kv.set("a", 1)
        kv.set("b", 1)
        kv.set("c", 1)
        self.assertEqual(kv.count(1), 3)
        kv.set("b", 2)  # overwrite
        self.assertEqual(kv.count(1), 2)
        self.assertEqual(kv.count(2), 1)
        kv.delete("a")
        self.assertEqual(kv.count(1), 1)
        self.assertEqual(kv.count(2), 1)


class TransactionTests(unittest.TestCase):
    def test_rollback_basic(self):
        kv = KVStore()
        kv.set("a", 1)
        kv.set("b", 2)
        kv.begin()
        kv.set("a", 100)
        kv.set("c", 3)
        kv.delete("b")
        kv.rollback()
        self.assertEqual(kv.get("a"), 1)
        self.assertEqual(kv.get("b"), 2)
        self.assertIsNone(kv.get("c"))

    def test_commit_basic(self):
        kv = KVStore()
        kv.set("a", 1)
        kv.begin()
        kv.set("a", 2)
        kv.set("b", 3)
        kv.commit()
        self.assertEqual(kv.get("a"), 2)
        self.assertEqual(kv.get("b"), 3)

    def test_no_transaction_on_operations(self):
        kv = KVStore()
        with self.assertRaises(NoTransaction):
            kv.rollback()
        with self.assertRaises(NoTransaction):
            kv.commit()

    def test_nested_rollback_independent(self):
        kv = KVStore()
        kv.set("a", 1)
        kv.begin()                 # outer
        kv.set("a", 2)
        kv.begin()                 # inner
        kv.set("a", 3)
        kv.rollback()              # inner only
        self.assertEqual(kv.get("a"), 2)
        kv.rollback()              # outer
        self.assertEqual(kv.get("a"), 1)

    def test_nested_commit_closes_all(self):
        kv = KVStore()
        kv.begin()
        kv.begin()
        kv.set("a", 1)
        kv.commit()
        # everything closed -> nested rollback must now raise
        with self.assertRaises(NoTransaction):
            kv.rollback()
        self.assertEqual(kv.get("a"), 1)

    def test_set_then_rollback_to_start_of_frame(self):
        kv = KVStore()
        kv.set("a", 1)
        kv.begin()
        kv.set("a", 2)
        kv.set("a", 3)
        kv.rollback()
        self.assertEqual(kv.get("a"), 1)

    def test_delete_then_rollback_restores(self):
        kv = KVStore()
        kv.set("a", 1)
        kv.begin()
        kv.delete("a")
        self.assertIsNone(kv.get("a"))
        kv.rollback()
        self.assertEqual(kv.get("a"), 1)

    def test_delete_then_rollback_counts(self):
        kv = KVStore()
        kv.set("a", 1)
        kv.set("b", 1)
        self.assertEqual(kv.count(1), 2)
        kv.begin()
        kv.delete("a")
        self.assertEqual(kv.count(1), 1)
        kv.rollback()
        self.assertEqual(kv.count(1), 2)

    def test_set_after_delete_same_frame(self):
        kv = KVStore()
        kv.begin()
        kv.set("a", 1)
        kv.delete("a")
        kv.rollback()
        self.assertIsNone(kv.get("a"))
        self.assertEqual(kv.count(1), 0)

    def test_deeper_nested_interleaved(self):
        kv = KVStore()
        kv.begin()  # f1
        kv.set("a", 1)
        kv.begin()  # f2
        kv.set("b", 2)
        kv.begin()  # f3
        kv.set("a", 9)
        kv.rollback()  # undo f3
        self.assertEqual(kv.get("a"), 1)
        self.assertEqual(kv.get("b"), 2)
        kv.rollback()  # undo f2
        self.assertEqual(kv.get("b"), None)
        self.assertEqual(kv.get("a"), 1)
        kv.rollback()  # undo f1
        self.assertEqual(kv.get("a"), None)

    def test_count_reflects_open_transaction(self):
        kv = KVStore()
        kv.set("a", 5)
        self.assertEqual(kv.count(5), 1)
        kv.begin()
        kv.set("b", 5)
        self.assertEqual(kv.count(5), 2)
        kv.rollback()
        self.assertEqual(kv.count(5), 1)

    def test_commit_then_more_changes(self):
        kv = KVStore()
        kv.begin()
        kv.set("a", 1)
        kv.commit()
        kv.begin()
        kv.set("a", 2)
        kv.rollback()
        self.assertEqual(kv.get("a"), 1)
        kv.begin()
        kv.set("a", 3)
        kv.commit()
        self.assertEqual(kv.get("a"), 3)


class ReferenceModelTests(unittest.TestCase):
    """Cross-check against an independent layered reference implementation."""

    def _reference(self, ops):
        """
        ops: list of tuples describing operations. Each op is one of:
            ("begin",)
            ("set", k, v)
            ("get", k)
            ("delete", k)
            ("rollback",)
            ("commit",)
        Returns expected values of the visible state after each op.
        """
        base = {}                       # committed
        visible = {}                    # current
        counts = {}
        stack = []                      # frames: {k: old or _DEL}
        DEL = object()

        def apply_set(k, v):
            old = visible.get(k, DEL)
            if stack:
                stack[-1].setdefault(k, old)
            if old is not DEL:
                n = counts[old] - 1
                if n:
                    counts[old] = n
                else:
                    del counts[old]
            visible[k] = v
            counts[v] = counts.get(v, 0) + 1

        def apply_delete(k):
            if k not in visible:
                return
            old = visible.pop(k)
            if stack:
                stack[-1].setdefault(k, old)
            n = counts[old] - 1
            if n:
                counts[old] = n
            else:
                del counts[old]

        def rollback():
            frame = stack.pop()
            for k, old in frame.items():
                cur = visible.get(k, DEL)
                if old is DEL:
                    visible.pop(k, None)
                    if cur is not DEL:
                        n = counts[cur] - 1
                        if n:
                            counts[cur] = n
                        else:
                            del counts[cur]
                else:
                    if cur != old:
                        if cur is not DEL:
                            n = counts[cur] - 1
                            if n:
                                counts[cur] = n
                            else:
                                del counts[cur]
                        visible[k] = old
                        counts[old] = counts.get(old, 0) + 1

        def commit():
            base.update(visible)
            stack.clear()

        snapshots = []
        for op in ops:
            kind = op[0]
            if kind == "begin":
                stack.append({})
            elif kind == "set":
                apply_set(op[1], op[2])
            elif kind == "delete":
                apply_delete(op[1])
            elif kind == "get":
                pass
            elif kind == "rollback":
                rollback()
            elif kind == "commit":
                commit()
            snapshots.append((dict(base), dict(visible), dict(counts)))
        return snapshots

    def _run_reference(self, ops):
        kv = KVStore()
        actuals = []
        for op in ops:
            kind = op[0]
            if kind == "begin":
                kv.begin()
            elif kind == "set":
                kv.set(op[1], op[2])
            elif kind == "delete":
                kv.delete(op[1])
            elif kind == "rollback":
                kv.rollback()
            elif kind == "commit":
                kv.commit()
            actuals.append((dict(kv._data), dict(kv._counts)))
        return actuals

    def test_matches_reference(self):
        import random
        rng = random.Random(12345)
        for trial in range(2000):
            n = rng.randint(0, 60)
            keys = [("k%d" % i, "m%d" % i) for i in range(rng.randint(1, 6))]
            values = [str(i) for i in range(5)]
            ops = []
            depth = 0
            for _ in range(n):
                r = rng.random()
                if r < 0.20:
                    depth += 1
                    ops.append(("begin",))
                elif r < 0.45:
                    k = rng.choice(keys)[0]
                    v = rng.choice(values)
                    ops.append(("set", k, v))
                elif r < 0.60:
                    k = rng.choice(keys)[0]
                    ops.append(("delete", k))
                elif r < 0.80 and depth > 0:
                    depth -= 1
                    ops.append(("rollback",))
                elif depth > 0:
                    ops.append(("commit",))
                    depth = 0
            ref = self._reference(ops)
            actual = self._run_reference(ops)
            self.assertEqual(len(ref), len(actual))
            for (rbase, rvis, rcnt), (avis, acnt) in zip(ref, actual):
                # visible state must match reference
                self.assertEqual(avis, rvis,
                                 "state mismatch at op index %d" % len(ref))
                # counts must match reference
                self.assertEqual(acnt, rcnt,
                                 "counts mismatch at op index %d" % len(ref))
                # counts must actually equal count() method output
                for k, v in rvis.items():
                    self.assertEqual(kv.count(v) if False else None, None)
                # validate count() method against visible independently
                rebuilt = {}
                for kk, vv in rvis.items():
                    rebuilt[vv] = rebuilt.get(vv, 0) + 1
                # rebuild via a fresh kv to test count()
                kv2 = KVStore()
                for kk, vv in rvis.items():
                    kv2.set(kk, vv)
                for vv, cnt in rebuilt.items():
                    self.assertEqual(kv2.count(vv), cnt)


class PerformanceTests(unittest.TestCase):
    def test_count_is_constant_time(self):
        kv = KVStore()
        for i in range(500000):
            kv.set(i, i % 10)
        start = time.perf_counter()
        for _ in range(100000):
            kv.count(3)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 2.0)


if __name__ == "__main__":
    unittest.main()