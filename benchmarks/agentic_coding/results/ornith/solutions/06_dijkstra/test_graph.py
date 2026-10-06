import math
import unittest

from graph import Graph


class TestGraph(unittest.TestCase):
    def test_add_node_noop(self):
        g = Graph()
        g.add_node("a")
        g.add_node("a")
        self.assertIn("a", g._neighbors)

    def test_add_edge_directed(self):
        g = Graph()
        g.add_edge("a", "b", 5)
        self.assertEqual(g._neighbors["a"], {"b": 5})
        self.assertIn("b", g._neighbors)
        self.assertNotIn("a", g._neighbors["b"])

    def test_add_edge_bidirectional(self):
        g = Graph()
        g.add_edge("a", "b", 5, bidirectional=True)
        self.assertEqual(g._neighbors["a"], {"b": 5})
        self.assertEqual(g._neighbors["b"], {"a": 5})

    def test_negative_weight(self):
        g = Graph()
        with self.assertRaises(ValueError):
            g.add_edge("a", "b", -1)

    def test_keep_minimum_weight(self):
        g = Graph()
        g.add_edge("a", "b", 5)
        g.add_edge("a", "b", 3)
        g.add_edge("a", "b", 7)
        self.assertEqual(g._neighbors["a"]["b"], 3)

    def test_zero_weight_allowed(self):
        g = Graph()
        g.add_edge("a", "b", 0)
        self.assertEqual(g._neighbors["a"]["b"], 0)

    def test_shortest_path_basic(self):
        g = Graph()
        g.add_edge("a", "b", 1)
        g.add_edge("b", "c", 2)
        g.add_edge("a", "c", 10)
        cost, path = g.shortest_path("a", "c")
        self.assertEqual(cost, 3)
        self.assertEqual(path, ["a", "b", "c"])

    def test_src_equals_dst(self):
        g = Graph()
        g.add_node("a")
        self.assertEqual(g.shortest_path("a", "a"), (0, ["a"]))

    def test_unreachable(self):
        g = Graph()
        g.add_edge("a", "b", 1)
        g.add_node("c")
        cost, path = g.shortest_path("a", "c")
        self.assertEqual(cost, math.inf)
        self.assertEqual(path, [])

    def test_missing_src(self):
        g = Graph()
        g.add_node("a")
        with self.assertRaises(KeyError):
            g.shortest_path("z", "a")

    def test_missing_dst(self):
        g = Graph()
        g.add_node("a")
        with self.assertRaises(KeyError):
            g.shortest_path("a", "z")

    def test_zero_weight_shortest(self):
        g = Graph()
        g.add_edge("a", "b", 5)
        g.add_edge("a", "c", 0)
        g.add_edge("c", "b", 0)
        cost, path = g.shortest_path("a", "b")
        self.assertEqual(cost, 0)

    def test_ties(self):
        g = Graph()
        g.add_edge("a", "b", 1)
        g.add_edge("a", "c", 1)
        g.add_edge("b", "d", 1)
        g.add_edge("c", "d", 1)
        cost, path = g.shortest_path("a", "d")
        self.assertEqual(cost, 2)
        self.assertEqual(path[0], "a")
        self.assertEqual(path[-1], "d")

    def test_hashable_nodes(self):
        g = Graph()
        g.add_edge((1, 2), (3, 4), 2)
        cost, path = g.shortest_path((1, 2), (3, 4))
        self.assertEqual(cost, 2)
        self.assertEqual(path, [(1, 2), (3, 4)])


if __name__ == "__main__":
    unittest.main()