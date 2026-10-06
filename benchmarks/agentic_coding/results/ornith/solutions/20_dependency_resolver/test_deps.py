import unittest

from deps import build_order, layers, affected, CycleError


def is_valid_build_order(deps, order):
    seen = set()
    for node in order:
        for dep in deps.get(node, ()):
            if dep not in seen:
                return False
        seen.add(node)
    return True


class BuildOrderTests(unittest.TestCase):
    def test_simple_diamond(self):
        deps = {"a": ["b", "c"], "b": ["c"], "c": [], "d": []}
        order = build_order(deps)
        self.assertEqual(set(order), {"a", "b", "c", "d"})
        self.assertTrue(is_valid_build_order(deps, order))

    def test_lexicographic_tiebreak(self):
        deps = {"a": [], "b": [], "c": []}
        self.assertEqual(build_order(deps), ["a", "b", "c"])

    def test_depends_only_as_dep(self):
        deps = {"a": ["b"]}
        order = build_order(deps)
        self.assertEqual(order, ["b", "a"])

    def test_duplicate_dependencies(self):
        deps = {"a": ["b", "b", "b"], "b": []}
        order = build_order(deps)
        self.assertEqual(order, ["b", "a"])

    def test_empty(self):
        self.assertEqual(build_order({}), [])

    def test_cycle_raises(self):
        with self.assertRaises(CycleError):
            build_order({"a": ["b"], "b": ["a"]})


class CycleTests(unittest.TestCase):
    def test_simple_cycle(self):
        try:
            build_order({"a": ["b"], "b": ["c"], "c": ["a"]})
            self.fail("expected CycleError")
        except CycleError as exc:
            cycle = exc.cycle
            self.assertEqual(cycle[0], cycle[-1])
            self.assertEqual(len(cycle), 4)
            self.assertTrue(self._is_valid_cycle(cycle))

    def _is_valid_cycle(self, cycle):
        for x, y in zip(cycle, cycle[1:]):
            if x not in {"a", "b", "c"}:
                return False
        return True

    def test_self_cycle(self):
        try:
            build_order({"a": ["a"]})
            self.fail("expected CycleError")
        except CycleError as exc:
            self.assertEqual(exc.cycle, ["a", "a"])

    def test_cycle_from_layers(self):
        with self.assertRaises(CycleError):
            layers({"a": ["b"], "b": ["a"]})

    def test_cycle_from_build_order_long(self):
        n = 50
        deps = {str(i): [str(i + 1)] for i in range(n)}
        deps[str(n)] = ["0"]
        with self.assertRaises(CycleError):
            build_order(deps)


class LayersTests(unittest.TestCase):
    def test_basic(self):
        deps = {"a": ["b", "c"], "b": ["c"], "c": []}
        result = layers(deps)
        self.assertEqual(result, [["c"], ["b"], ["a"]])

    def test_widest_layer_sorted(self):
        deps = {"a": [], "b": [], "c": [], "d": ["a", "b"]}
        self.assertEqual(layers(deps), [["a", "b", "c"], ["d"]])

    def test_no_deps_all_zero(self):
        self.assertEqual(layers({"a": [], "b": []}), [["a", "b"]])

    def test_empty(self):
        self.assertEqual(layers({}), [])

    def test_cycle_raises(self):
        with self.assertRaises(CycleError):
            layers({"a": ["b"], "b": ["c"], "c": ["a"]})

    def test_deep_chain(self):
        n = 200
        deps = {"node_%d" % i: ["node_%d" % (i - 1)] for i in range(1, n)}
        deps["node_0"] = []
        result = layers(deps)
        self.assertEqual(len(result), n)
        self.assertEqual(result[0], ["node_0"])
        self.assertEqual(result[-1], ["node_%d" % (n - 1)])


class AffectedTests(unittest.TestCase):
    def test_transitive_dependents(self):
        deps = {"a": ["b"], "b": ["c"], "c": [], "d": ["b"]}
        result = affected(deps, {"c"})
        self.assertEqual(result, {"a", "b", "c", "d"})

    def test_only_direct(self):
        deps = {"a": ["b"], "b": [], "c": []}
        self.assertEqual(affected(deps, {"b"}), {"a", "b"})

    def test_changed_not_in_deps(self):
        self.assertEqual(affected({}, {"x"}), {"x"})

    def test_empty(self):
        self.assertEqual(affected({}, set()), set())

    def test_no_dependents(self):
        deps = {"a": []}
        self.assertEqual(affected(deps, {"a"}), {"a"})

    def test_multiple_seeds(self):
        deps = {"a": ["b"], "b": ["c"], "c": [], "d": ["e"], "e": []}
        self.assertEqual(affected(deps, {"c", "e"}), {"a", "b", "c", "d", "e"})


class PerformanceTests(unittest.TestCase):
    def test_large_dag_no_recursion(self):
        n = 10000
        deps = {}
        for i in range(n):
            deps["n%d" % i] = ["n%d" % (i - 1)] if i > 0 else []
        order = build_order(deps)
        self.assertEqual(len(order), n)
        self.assertEqual(order[0], "n0")
        self.assertEqual(order[-1], "n9999")

    def test_deep_chain_layers(self):
        n = 5000
        deps = {"n%d" % i: ["n%d" % (i - 1)] for i in range(1, n)}
        deps["n0"] = []
        result = layers(deps)
        self.assertEqual(len(result), n)

    def test_long_cycle_detection(self):
        n = 5000
        deps = {"n%d" % i: ["n%d" % (i + 1)] for i in range(n - 1)}
        deps["n%d" % (n - 1)] = ["n0"]
        try:
            build_order(deps)
            self.fail("expected CycleError")
        except CycleError as exc:
            cycle = exc.cycle
            self.assertEqual(cycle[0], cycle[-1])
            self.assertEqual(len(cycle), n + 1)


if __name__ == "__main__":
    unittest.main()