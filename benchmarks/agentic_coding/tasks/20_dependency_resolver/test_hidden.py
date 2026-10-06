import unittest, random
from deps import build_order, layers, affected, CycleError


def valid_order(tc, deps, order):
    pos = {n: i for i, n in enumerate(order)}
    nodes = set(deps) | {d for v in deps.values() for d in v}
    tc.assertEqual(set(order), nodes); tc.assertEqual(len(order), len(nodes))
    for k, vs in deps.items():
        for v in vs: tc.assertLess(pos[v], pos[k])


def valid_cycle(tc, deps, cyc):
    tc.assertGreaterEqual(len(cyc), 2); tc.assertEqual(cyc[0], cyc[-1])
    for x, y in zip(cyc, cyc[1:]): tc.assertIn(y, set(deps.get(x, ())))


class T(unittest.TestCase):
    def test_order(self):
        d = {'app': ['lib', 'utils'], 'lib': ['utils', 'core'], 'utils': ['core'], 'tests': ['app']}
        self.assertEqual(build_order(d), ['core', 'utils', 'lib', 'app', 'tests'])

    def test_lexicographic(self):
        self.assertEqual(build_order({'b': [], 'a': [], 'c': ['b'], 'd': ['a']}), ['a', 'b', 'c', 'd'])
        self.assertEqual(build_order({'z': ['y'], 'y': [], 'a': ['z']}), ['y', 'z', 'a'])

    def test_dep_only_nodes_and_dupes(self): self.assertEqual(build_order({'x': ['y', 'y', 'z']}), ['y', 'z', 'x'])
    def test_empty(self): self.assertEqual(build_order({}), []); self.assertEqual(layers({}), [])

    def test_cycle(self):
        d = {'a': ['b'], 'b': ['c'], 'c': ['a'], 'd': ['a']}
        with self.assertRaises(CycleError) as cm: build_order(d)
        valid_cycle(self, d, cm.exception.cycle); self.assertTrue(issubclass(CycleError, ValueError))

    def test_self_cycle(self):
        with self.assertRaises(CycleError) as cm: build_order({'a': ['a']})
        self.assertEqual(cm.exception.cycle, ['a', 'a'])

    def test_layers(self):
        d = {'app': ['lib', 'utils'], 'lib': ['core'], 'utils': ['core'], 'tool': ['core'], 'docs': []}
        self.assertEqual(layers(d), [['core', 'docs'], ['lib', 'tool', 'utils'], ['app']])
        with self.assertRaises(CycleError): layers({'a': ['b'], 'b': ['a']})

    def test_affected(self):
        d = {'app': ['lib'], 'lib': ['core'], 'cli': ['core'], 'other': []}
        self.assertEqual(affected(d, ['lib']), {'lib', 'app'}); self.assertEqual(affected(d, {'core'}), {'core', 'lib', 'app', 'cli'})
        self.assertEqual(affected(d, []), set())

    def test_random_valid(self):
        rnd = random.Random(4)
        for _ in range(30):
            n = rnd.randint(1, 40); names = ['n%02d' % i for i in range(n)]
            d = {names[i]: rnd.sample(names[:i], rnd.randint(0, min(i, 4))) for i in range(n) if rnd.random() < 0.9}
            valid_order(self, d, build_order(d))
            lay = layers(d); flat = [x for l in lay for x in l]; valid_order(self, d, flat)

    def test_deep_chain(self):
        n = 6000; d = {'n%05d' % i: ['n%05d' % (i - 1)] for i in range(1, n)}
        self.assertEqual(build_order(d)[0], 'n00000'); self.assertEqual(len(layers(d)), n)
        self.assertEqual(len(affected(d, ['n00000'])), n)

    def test_long_cycle(self):
        n = 5000; d = {'n%05d' % i: ['n%05d' % ((i + 1) % n)] for i in range(n)}
        with self.assertRaises(CycleError) as cm: build_order(d)
        valid_cycle(self, d, cm.exception.cycle); self.assertEqual(len(cm.exception.cycle), n + 1)
