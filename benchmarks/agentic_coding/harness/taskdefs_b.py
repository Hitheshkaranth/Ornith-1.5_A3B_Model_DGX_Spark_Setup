TASKS = []

# ---------------------------------------------------------------- 06
TASKS.append(dict(
id="06_dijkstra", difficulty="easy",
prompt=r'''Create `graph.py` with class `Graph` (weighted directed graph):

- `add_node(u)`: add an isolated node (no-op if present). Nodes are any hashable values.
- `add_edge(u, v, w, bidirectional=False)`: adds nodes as needed and an edge u->v with weight `w` (also v->u if bidirectional).
  Negative weight raises `ValueError`. If an edge u->v already exists keep the MINIMUM weight. Zero weights are allowed.
- `shortest_path(src, dst) -> tuple[cost, list]`: returns `(cost, [src, ..., dst])` for a minimum-cost path.
  If `src == dst` return `(0, [src])`. If `dst` is unreachable return `(math.inf, [])`.
  If `src` or `dst` is not a node of the graph raise `KeyError`.
''',
starter={},
ref={"graph.py": r'''import heapq
import math


class Graph:
    def __init__(self):
        self.adj = {}

    def add_node(self, u):
        self.adj.setdefault(u, {})

    def add_edge(self, u, v, w, bidirectional=False):
        if w < 0:
            raise ValueError("negative weight")
        self.add_node(u); self.add_node(v)
        if w < self.adj[u].get(v, math.inf):
            self.adj[u][v] = w
        if bidirectional and w < self.adj[v].get(u, math.inf):
            self.adj[v][u] = w

    def shortest_path(self, src, dst):
        if src not in self.adj or dst not in self.adj:
            raise KeyError(src if src not in self.adj else dst)
        dist, prev, done = {src: 0}, {}, set()
        pq, cnt = [(0, 0, src)], 1
        while pq:
            d, _, u = heapq.heappop(pq)
            if u in done:
                continue
            done.add(u)
            if u == dst:
                break
            for v, w in self.adj[u].items():
                nd = d + w
                if v not in dist or nd < dist[v]:
                    dist[v] = nd; prev[v] = u
                    heapq.heappush(pq, (nd, cnt, v)); cnt += 1
        if dst not in dist:
            return (math.inf, [])
        path = [dst]
        while path[-1] != src:
            path.append(prev[path[-1]])
        return (dist[dst], path[::-1])
'''},
tests=r'''import unittest, math, random
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
'''))

# ---------------------------------------------------------------- 07
TASKS.append(dict(
id="07_token_bucket", difficulty="easy",
prompt=r'''Create `ratelimit.py`:

`TokenBucket(rate: float, capacity: float, clock=time.monotonic)`
- `rate` = tokens added per second (must be > 0), `capacity` = max tokens (must be > 0); otherwise `ValueError`.
- The bucket starts FULL. Tokens refill continuously based on `clock()` and are capped at `capacity`.
- `allow(n=1) -> bool`: if at least `n` tokens are available consume them and return True; otherwise return False and consume nothing.
- `wait_time(n=1) -> float`: seconds until `n` tokens will be available (0.0 if available now). Does not consume.
- For both methods, `n <= 0` or `n > capacity` raises `ValueError`.
- `tokens` property: current (float) number of tokens.

`KeyedLimiter(rate, capacity, clock=time.monotonic)`
- `allow(key, n=1) -> bool`: an independent TokenBucket per key, created (full) on first use.
''',
starter={},
ref={"ratelimit.py": r'''import time


class TokenBucket:
    def __init__(self, rate, capacity, clock=time.monotonic):
        if rate <= 0 or capacity <= 0:
            raise ValueError("rate and capacity must be > 0")
        self.rate, self.capacity, self.clock = rate, capacity, clock
        self._tokens = float(capacity)
        self._last = clock()

    def _refill(self):
        now = self.clock()
        self._tokens = min(self.capacity, self._tokens + (now - self._last) * self.rate)
        self._last = now

    def _check(self, n):
        if n <= 0 or n > self.capacity:
            raise ValueError("bad n")

    @property
    def tokens(self):
        self._refill()
        return self._tokens

    def allow(self, n=1):
        self._check(n); self._refill()
        if self._tokens >= n:
            self._tokens -= n
            return True
        return False

    def wait_time(self, n=1):
        self._check(n); self._refill()
        return max(0.0, (n - self._tokens) / self.rate)


class KeyedLimiter:
    def __init__(self, rate, capacity, clock=time.monotonic):
        TokenBucket(rate, capacity, clock)
        self.rate, self.capacity, self.clock = rate, capacity, clock
        self._b = {}

    def allow(self, key, n=1):
        if key not in self._b:
            self._b[key] = TokenBucket(self.rate, self.capacity, self.clock)
        return self._b[key].allow(n)
'''},
tests=r'''import unittest
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
'''))

# ---------------------------------------------------------------- 08
TASKS.append(dict(
id="08_semver", difficulty="medium",
prompt=r'''Create `semver.py` implementing Semantic Versioning 2.0.0 parsing, comparison and ranges.

- `parse(v: str) -> tuple`: returns `(major, minor, patch, prerelease)` where `prerelease` is a tuple of the dot-separated
  prerelease identifiers as strings (empty tuple if none). Build metadata (`+...`) is accepted and dropped.
  Example: `parse("1.2.3-alpha.1+build.5") == (1, 2, 3, ("alpha", "1"))`.
  Invalid versions raise `ValueError`: must be exactly `X.Y.Z` with no leading zeros in numeric parts, no `v` prefix,
  prerelease identifiers non-empty, numeric prerelease identifiers without leading zeros.
- `compare(a: str, b: str) -> int`: -1, 0 or 1 following SemVer precedence rules (prerelease < release; identifiers compared
  numerically when both numeric, numeric < alphanumeric, else ASCII order; a shorter prefix set has lower precedence).
  Build metadata is ignored.
- `satisfies(version: str, range: str) -> bool`:
  * A range is one or more alternatives separated by `||`; an alternative is one or more whitespace-separated comparators that must ALL hold.
  * Comparators: `>=V`, `>V`, `<=V`, `<V`, `=V`, bare `V` (exact), `^V`, `~V`, and `*` (matches anything). V is always a full X.Y.Z[-pre].
  * Caret: `^1.2.3` := `>=1.2.3 <2.0.0`; `^0.2.3` := `>=0.2.3 <0.3.0`; `^0.0.3` := `>=0.0.3 <0.0.4`.
  * Tilde: `~1.2.3` := `>=1.2.3 <1.3.0`.
  * Use plain `compare` semantics (no special prerelease exclusion rules).
  * A malformed range (empty, bad version in a comparator) raises `ValueError`.
''',
starter={},
ref={"semver.py": r'''import re

_ID = r'(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)'
_RE = re.compile(r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-(' + _ID + r'(?:\.' + _ID + r')*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$')


def parse(v):
    m = _RE.match(v) if isinstance(v, str) else None
    if not m:
        raise ValueError("invalid version %r" % (v,))
    pre = tuple(m.group(4).split('.')) if m.group(4) else ()
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)), pre)


def _cmp_pre(a, b):
    if a == b: return 0
    if not a: return 1
    if not b: return -1
    for x, y in zip(a, b):
        if x == y: continue
        xd, yd = x.isdigit(), y.isdigit()
        if xd and yd: return -1 if int(x) < int(y) else 1
        if xd: return -1
        if yd: return 1
        return -1 if x < y else 1
    return -1 if len(a) < len(b) else 1


def compare(a, b):
    pa, pb = parse(a), parse(b)
    if pa[:3] != pb[:3]:
        return -1 if pa[:3] < pb[:3] else 1
    return _cmp_pre(pa[3], pb[3])


def _split(comp):
    if comp == '*':
        return '*', None
    for op in ('>=', '<=', '>', '<', '=', '^', '~'):
        if comp.startswith(op):
            t = comp[len(op):]; parse(t); return op, t
    parse(comp)
    return '=', comp


def _ok(v, op, t):
    if op == '*': return True
    c = compare(v, t)
    if op == '>=': return c >= 0
    if op == '>': return c > 0
    if op == '<=': return c <= 0
    if op == '<': return c < 0
    if op == '=': return c == 0
    M, m, p, _ = parse(t)
    if op == '^':
        up = "%d.0.0" % (M + 1) if M > 0 else ("0.%d.0" % (m + 1) if m > 0 else "0.0.%d" % (p + 1))
    else:
        up = "%d.%d.0" % (M, m + 1)
    return c >= 0 and compare(v, up) < 0


def satisfies(version, rng):
    parse(version)
    alts = []
    for alt in rng.split('||'):
        comps = alt.split()
        if not comps:
            raise ValueError("empty range")
        alts.append([_split(c) for c in comps])
    return any(all(_ok(version, op, t) for op, t in alt) for alt in alts)
'''},
tests=r'''import unittest
from semver import parse, compare, satisfies

ORDER = ["1.0.0-alpha", "1.0.0-alpha.1", "1.0.0-alpha.beta", "1.0.0-beta", "1.0.0-beta.2", "1.0.0-beta.11",
         "1.0.0-rc.1", "1.0.0", "1.0.1", "1.1.0", "1.9.0", "1.10.0", "2.0.0", "10.0.0"]


class T(unittest.TestCase):
    def test_order(self):
        for i, a in enumerate(ORDER):
            self.assertEqual(compare(a, a), 0)
            for b in ORDER[i + 1:]:
                self.assertEqual(compare(a, b), -1, (a, b)); self.assertEqual(compare(b, a), 1, (b, a))

    def test_parse(self):
        self.assertEqual(parse("1.2.3-alpha.1+build.5"), (1, 2, 3, ("alpha", "1")))
        self.assertEqual(parse("1.2.3"), (1, 2, 3, ()))
        self.assertEqual(parse("0.0.0+x"), (0, 0, 0, ()))

    def test_build_ignored(self): self.assertEqual(compare("1.0.0+a", "1.0.0+b"), 0)

    def test_invalid(self):
        for bad in ["1.2", "1.2.3.4", "01.2.3", "1.02.3", "1.2.3-", "a.b.c", "1.2.3-01", "", "v1.2.3", "1.2.3-a..b", "1.2.3+"]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError): parse(bad)

    def test_caret(self):
        self.assertTrue(satisfies("1.9.9", "^1.2.3")); self.assertFalse(satisfies("2.0.0", "^1.2.3")); self.assertFalse(satisfies("1.2.2", "^1.2.3"))
        self.assertTrue(satisfies("0.2.9", "^0.2.3")); self.assertFalse(satisfies("0.3.0", "^0.2.3"))
        self.assertTrue(satisfies("0.0.3", "^0.0.3")); self.assertFalse(satisfies("0.0.4", "^0.0.3"))

    def test_tilde(self):
        self.assertTrue(satisfies("1.2.9", "~1.2.3")); self.assertFalse(satisfies("1.3.0", "~1.2.3")); self.assertFalse(satisfies("1.2.2", "~1.2.3"))

    def test_compound(self):
        self.assertTrue(satisfies("1.5.0", ">=1.2.0 <2.0.0")); self.assertFalse(satisfies("2.0.0", ">=1.2.0 <2.0.0"))
        self.assertTrue(satisfies("3.1.0", "^1.0.0 || >=3.0.0")); self.assertFalse(satisfies("2.5.0", "^1.0.0 || >=3.0.0"))
        self.assertTrue(satisfies("1.0.0", ">=1.0.0  <=1.0.0"))

    def test_exact_and_ops(self):
        self.assertTrue(satisfies("1.2.3", "1.2.3")); self.assertFalse(satisfies("1.2.3", "=1.2.4")); self.assertTrue(satisfies("1.2.3+build", "=1.2.3"))
        self.assertFalse(satisfies("1.2.3", ">1.2.3")); self.assertTrue(satisfies("1.2.3", "<=1.2.3")); self.assertTrue(satisfies("1.0.0-rc.1", "<1.0.0"))

    def test_star(self): self.assertTrue(satisfies("4.5.6", "*"))

    def test_bad_range(self):
        for r in [">=abc", "^1.2", "", "1.0.0 || ", ">= 1.0.0"]:
            with self.subTest(r=r):
                with self.assertRaises(ValueError): satisfies("1.0.0", r)
'''))

# ---------------------------------------------------------------- 09
TASKS.append(dict(
id="09_json_parser", difficulty="hard",
prompt=r'''Create `minijson.py` with `loads(s: str)` — a strict JSON (RFC 8259) parser. Do NOT use the `json` module.

- Return Python values exactly like `json.loads` would: dict (later duplicate keys win, key order preserved), list, str, int
  (for numbers without fraction/exponent), float (otherwise), True, False, None.
- Strings: escapes `\" \\ \/ \b \f \n \r \t \uXXXX`; a `\uXXXX` high surrogate followed by a `\uXXXX` low surrogate combines
  into one code point. Raw control characters (< U+0020) inside strings are invalid.
- Numbers: `-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?` only (no leading `+`, no leading zeros, no `.5`, no `1.`, no hex, no NaN/Infinity).
- Whitespace allowed between tokens: space, tab, `\n`, `\r`.
- Anything invalid (trailing commas, single quotes, unquoted keys, trailing garbage, unterminated input, bad escapes, ...) raises `ValueError`.
''',
starter={},
ref={"minijson.py": r'''import re

_NUM = re.compile(r'-?(?:0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?')
_ESC = {'"': '"', '\\': '\\', '/': '/', 'b': '\b', 'f': '\f', 'n': '\n', 'r': '\r', 't': '\t'}
_HEX = set('0123456789abcdefABCDEF')


class _P:
    def __init__(s, t): s.t, s.i = t, 0
    def err(s, m): raise ValueError("%s at %d" % (m, s.i))

    def ws(s):
        while s.i < len(s.t) and s.t[s.i] in ' \t\n\r': s.i += 1

    def value(s):
        s.ws()
        if s.i >= len(s.t): s.err("unexpected end")
        c = s.t[s.i]
        if c == '{': return s.obj()
        if c == '[': return s.arr()
        if c == '"': return s.string()
        if c == '-' or c in '0123456789': return s.num()
        for lit, val in (('true', True), ('false', False), ('null', None)):
            if s.t.startswith(lit, s.i):
                s.i += len(lit); return val
        s.err("unexpected character")

    def num(s):
        m = _NUM.match(s.t, s.i)
        if not m: s.err("bad number")
        s.i = m.end(); txt = m.group(0)
        return float(txt) if (m.group(1) or m.group(2)) else int(txt)

    def obj(s):
        s.i += 1; d = {}; s.ws()
        if s.i < len(s.t) and s.t[s.i] == '}':
            s.i += 1; return d
        while True:
            s.ws()
            if s.i >= len(s.t) or s.t[s.i] != '"': s.err("expected key")
            k = s.string(); s.ws()
            if s.i >= len(s.t) or s.t[s.i] != ':': s.err("expected :")
            s.i += 1; d[k] = s.value(); s.ws()
            if s.i < len(s.t) and s.t[s.i] == ',':
                s.i += 1; continue
            if s.i < len(s.t) and s.t[s.i] == '}':
                s.i += 1; return d
            s.err("expected , or }")

    def arr(s):
        s.i += 1; a = []; s.ws()
        if s.i < len(s.t) and s.t[s.i] == ']':
            s.i += 1; return a
        while True:
            a.append(s.value()); s.ws()
            if s.i < len(s.t) and s.t[s.i] == ',':
                s.i += 1; continue
            if s.i < len(s.t) and s.t[s.i] == ']':
                s.i += 1; return a
            s.err("expected , or ]")

    def hex4(s):
        h = s.t[s.i + 1:s.i + 5]
        if len(h) != 4 or any(ch not in _HEX for ch in h): s.err("bad \\u escape")
        s.i += 5; return int(h, 16)

    def string(s):
        s.i += 1; out = []
        while True:
            if s.i >= len(s.t): s.err("unterminated string")
            c = s.t[s.i]
            if c == '"':
                s.i += 1; return ''.join(out)
            if c == '\\':
                s.i += 1
                if s.i >= len(s.t): s.err("unterminated escape")
                e = s.t[s.i]
                if e in _ESC:
                    out.append(_ESC[e]); s.i += 1
                elif e == 'u':
                    cp = s.hex4()
                    if 0xD800 <= cp <= 0xDBFF and s.t.startswith('\\u', s.i):
                        save = s.i; s.i += 1; lo = s.hex4()
                        if 0xDC00 <= lo <= 0xDFFF:
                            cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00)
                        else:
                            s.i = save
                    out.append(chr(cp))
                else:
                    s.err("bad escape")
            elif ord(c) < 0x20:
                s.err("control character in string")
            else:
                out.append(c); s.i += 1


def loads(s):
    p = _P(s)
    v = p.value(); p.ws()
    if p.i != len(s): p.err("trailing data")
    return v
'''},
tests=r'''import unittest, json, random, pathlib
from minijson import loads

VALID = ['0', '-0', '12', '-3.5', '1e3', '1E-2', '2.5e+3', '"abc"', '""', 'true', 'false', 'null', '[]', '{}',
         ' [1, 2 ,3] ', '{"a":1,"b":[true,false,null],"c":{"d":"e"}}',
         r'"esc \" \\ \/ \b \f \n \r \t"', r'"é中"', r'"😀"', r'"😀x"', '[[[[]]]]',
         '{"a":1,"a":2}', '"unicode é 中 \U0001F600"', '[1.5e10, -0.0, 0.25, 1E400]', '{"":""}',
         '  \n\t{ "x" : [ ] }  \r\n', '-12.5e-3', '[0,1,-1]']

INVALID = ['', ' ', '01', '1.', '.5', '+1', '[1,]', '{"a":1,}', "{'a':1}", '{"a" 1}', '[1 2]', '"abc', r'"\x"',
           r'"\u12"', r'"\u12G4"', 'tru', 'nul', 'NaN', 'Infinity', '-Infinity', '[1]]', '{"a":1}x', '"a\nb"', '"tab\there"',
           '-', '1e', '1e+', '{1:2}', '[', '{"a":}', '--1', '0x10', '[,1]', '{,}', 'True', '"\\']


def gen(rnd, depth=0):
    k = rnd.randint(0, 7 if depth < 4 else 4)
    if k == 0: return rnd.randint(-10**12, 10**12)
    if k == 1: return rnd.uniform(-1e6, 1e6)
    if k == 2: return ''.join(rnd.choice('ab"\\/\n\té中\U0001F600 \x01') for _ in range(rnd.randint(0, 8)))
    if k == 3: return rnd.choice([True, False, None])
    if k == 4: return rnd.random() * 10 ** rnd.randint(-30, 30)
    if k in (5, 6): return [gen(rnd, depth + 1) for _ in range(rnd.randint(0, 4))]
    return {''.join(rnd.choice('kxyé') for _ in range(rnd.randint(0, 3))): gen(rnd, depth + 1) for _ in range(rnd.randint(0, 4))}


class T(unittest.TestCase):
    def same(self, s):
        self.assertEqual(json.dumps(loads(s)), json.dumps(json.loads(s)), s)

    def test_valid(self):
        for s in VALID:
            with self.subTest(s=s): self.same(s)

    def test_invalid(self):
        for s in INVALID:
            with self.subTest(s=s):
                with self.assertRaises(ValueError): loads(s)

    def test_types(self):
        self.assertIs(type(loads('1')), int); self.assertIs(type(loads('1.0')), float); self.assertIs(type(loads('1e2')), float)

    def test_nested(self):
        s = '[' * 150 + ']' * 150; self.same(s)

    def test_random_roundtrip(self):
        rnd = random.Random(11)
        for _ in range(300):
            v = gen(rnd)
            s = json.dumps(v, ensure_ascii=rnd.random() < 0.5, indent=rnd.choice([None, 2]))
            self.same(s)

    def test_no_json_module(self):
        src = pathlib.Path(__import__('minijson').__file__).read_text(encoding="utf-8")
        self.assertNotIn('import json', src); self.assertNotIn('from json', src)
'''))

# ---------------------------------------------------------------- 10
TASKS.append(dict(
id="10_edit_distance", difficulty="medium",
prompt=r'''Create `editdist.py`:

- `levenshtein(a: str, b: str) -> int`: minimum number of single-character insertions, deletions and substitutions.
- `alignment(a: str, b: str) -> list[tuple]`: an optimal edit script as a list of ops, in order, that transforms `a` into `b`:
  `('keep', ch)`, `('sub', old_ch, new_ch)`, `('ins', ch)`, `('del', ch)`. Applying the ops left to right while walking
  through `a` must produce `b`, and the number of non-`keep` ops must equal `levenshtein(a, b)`.
- `osa_distance(a: str, b: str) -> int`: optimal string alignment distance = Levenshtein plus transposition of two ADJACENT
  characters at cost 1, where no substring is edited more than once (e.g. `osa_distance("ca", "abc") == 3`, `osa_distance("ab", "ba") == 1`).
- `closest(word: str, candidates: list[str], max_distance: int | None = None) -> list[str]`: the candidates having the minimal
  Levenshtein distance to `word`, in their original order; candidates farther than `max_distance` are excluded; `[]` if none qualify.
- Must handle two 1000-character strings in a few seconds.
''',
starter={},
ref={"editdist.py": r'''def _table(a, b):
    n, m = len(a), len(b)
    D = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1): D[i][0] = i
    for j in range(m + 1): D[0][j] = j
    for i in range(1, n + 1):
        ai, row, prev = a[i - 1], D[i], D[i - 1]
        for j in range(1, m + 1):
            row[j] = min(prev[j] + 1, row[j - 1] + 1, prev[j - 1] + (ai != b[j - 1]))
    return D


def levenshtein(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def alignment(a, b):
    D = _table(a, b); ops = []; i, j = len(a), len(b)
    while i or j:
        if i and j and D[i][j] == D[i - 1][j - 1] + (a[i - 1] != b[j - 1]):
            ops.append(('keep', a[i - 1]) if a[i - 1] == b[j - 1] else ('sub', a[i - 1], b[j - 1])); i -= 1; j -= 1
        elif i and D[i][j] == D[i - 1][j] + 1:
            ops.append(('del', a[i - 1])); i -= 1
        else:
            ops.append(('ins', b[j - 1])); j -= 1
    return ops[::-1]


def osa_distance(a, b):
    n, m = len(a), len(b)
    D = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1): D[i][0] = i
    for j in range(m + 1): D[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            c = a[i - 1] != b[j - 1]
            D[i][j] = min(D[i - 1][j] + 1, D[i][j - 1] + 1, D[i - 1][j - 1] + c)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                D[i][j] = min(D[i][j], D[i - 2][j - 2] + 1)
    return D[n][m]


def closest(word, candidates, max_distance=None):
    scored = [(levenshtein(word, c), c) for c in candidates]
    scored = [(d, c) for d, c in scored if max_distance is None or d <= max_distance]
    if not scored:
        return []
    best = min(d for d, _ in scored)
    return [c for d, c in scored if d == best]
'''},
tests=r'''import unittest, random, time
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
'''))
