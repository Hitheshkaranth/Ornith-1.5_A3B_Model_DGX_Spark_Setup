import unittest, math, random
from graph import Graph


class T(unittest.TestCase):
    def check(self, g, edges, src, dst, exp):
        cost, path = g.shortest_path(src, dst)
        self.assertAlmostEqual(cost, exp)
        if exp == math.inf:
            self.assertEqual(path, []); return
        self.assertEqual(path[0], src); self.assertEqual(path[-1], dst)
        self.assertAlmostEqual(sum(edges[(a, b)] for a, b in zip(path, path[1:])), exp)

    def test_simple(self):
        g = Graph(); E = {}
        for u, v, w in [('a', 'b', 4), ('a', 'c', 1), ('c', 'b', 2), ('b', 'd', 1), ('c', 'd', 5)]:
            g.add_edge(u, v, w); E[(u, v)] = w
        self.check(g, E, 'a', 'd', 4); self.assertEqual(g.shortest_path('a', 'd')[1], ['a', 'c', 'b', 'd'])

    def test_directed(self):
        g = Graph(); g.add_edge('a', 'b', 1); self.assertEqual(g.shortest_path('b', 'a'), (math.inf, []))

    def test_bidirectional(self):
        g = Graph(); g.add_edge('a', 'b', 3, bidirectional=True); self.assertEqual(tuple(g.shortest_path('b', 'a')), (3, ['b', 'a']))

    def test_same(self):
        g = Graph(); g.add_node('x'); self.assertEqual(tuple(g.shortest_path('x', 'x')), (0, ['x']))

    def test_unknown(self):
        g = Graph(); g.add_edge('a', 'b', 1)
        with self.assertRaises(KeyError): g.shortest_path('a', 'zz')
        with self.assertRaises(KeyError): g.shortest_path('zz', 'a')

    def test_negative(self):
        with self.assertRaises(ValueError): Graph().add_edge('a', 'b', -1)

    def test_parallel_min(self):
        g = Graph(); g.add_edge('a', 'b', 5); g.add_edge('a', 'b', 2); g.add_edge('a', 'b', 7)
        self.assertEqual(g.shortest_path('a', 'b')[0], 2)

    def test_isolated(self):
        g = Graph(); g.add_edge('a', 'b', 1); g.add_node('z'); self.assertEqual(tuple(g.shortest_path('a', 'z')), (math.inf, []))

    def test_random_vs_floyd(self):
        rnd = random.Random(3)
        for _ in range(20):
            n = rnd.randint(2, 12); nodes = list(range(n)); g = Graph(); E = {}
            for v in nodes: g.add_node(v)
            for _ in range(rnd.randint(0, n * 3)):
                u, v = rnd.choice(nodes), rnd.choice(nodes)
                if u == v: continue
                w = rnd.choice([0, 1, 2, 3, 5, 8, 1.5]); g.add_edge(u, v, w); E[(u, v)] = min(w, E.get((u, v), math.inf))
            Dm = {(i, j): (0 if i == j else E.get((i, j), math.inf)) for i in nodes for j in nodes}
            for k in nodes:
                for i in nodes:
                    for j in nodes:
                        if Dm[i, k] + Dm[k, j] < Dm[i, j]: Dm[i, j] = Dm[i, k] + Dm[k, j]
            for i in nodes:
                for j in nodes: self.check(g, E, i, j, Dm[i, j])
