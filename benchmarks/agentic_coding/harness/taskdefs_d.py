TASKS = []

# ---------------------------------------------------------------- 16
TASKS.append(dict(
id="16_business_days_bugfix", difficulty="easy",
prompt=r'''`bizdays.py` produces wrong dates in our invoicing system. Fix it to match this spec (keep function names/signatures):

- Business days are Monday-Friday that are not in `holidays` (an iterable of `datetime.date`; lists, sets and tuples must all work).
- `is_business_day(d, holidays=())`.
- `add_business_days(start, n, holidays=())`: for n > 0 move forward n business days, for n < 0 move backward |n| business days
  (the start day itself is never counted). For n == 0 return `start` if it is a business day, else the next business day.
- `business_days_between(a, b, holidays=())`: number of business days d with a <= d < b (end exclusive). If b < a return the
  negative of `business_days_between(b, a, holidays)`.
- `next_business_day(d, holidays=())`: the first business day strictly after d.
''',
starter={"bizdays.py": r'''from datetime import date, timedelta


def is_business_day(d, holidays=()):
    return d.weekday() < 6 and d not in holidays


def add_business_days(start, n, holidays=()):
    d = start
    while n > 0:
        d += timedelta(days=1)
        if is_business_day(d):
            n -= 1
    return d


def business_days_between(a, b, holidays=()):
    count = 0
    d = a
    while d <= b:
        if is_business_day(d, holidays):
            count += 1
        d += timedelta(days=1)
    return count


def next_business_day(d, holidays=()):
    return add_business_days(d, 1)
'''},
ref={"bizdays.py": r'''from datetime import date, timedelta


def is_business_day(d, holidays=()):
    return d.weekday() < 5 and d not in set(holidays)


def add_business_days(start, n, holidays=()):
    hol = set(holidays)
    d = start
    if n == 0:
        while not is_business_day(d, hol):
            d += timedelta(days=1)
        return d
    step = timedelta(days=1 if n > 0 else -1)
    n = abs(n)
    while n > 0:
        d += step
        if is_business_day(d, hol):
            n -= 1
    return d


def business_days_between(a, b, holidays=()):
    if b < a:
        return -business_days_between(b, a, holidays)
    hol = set(holidays)
    count, d = 0, a
    while d < b:
        if is_business_day(d, hol):
            count += 1
        d += timedelta(days=1)
    return count


def next_business_day(d, holidays=()):
    return add_business_days(d, 1, holidays)
'''},
tests=r'''import unittest
from datetime import date
from bizdays import is_business_day, add_business_days, business_days_between, next_business_day

TUE, FRI, SAT, SUN, MON = date(2026, 10, 6), date(2026, 10, 9), date(2026, 10, 10), date(2026, 10, 11), date(2026, 10, 12)


class T(unittest.TestCase):
    def test_is_business(self):
        self.assertTrue(is_business_day(TUE)); self.assertFalse(is_business_day(SAT)); self.assertFalse(is_business_day(SUN))
        self.assertFalse(is_business_day(TUE, [TUE]))

    def test_add_forward(self):
        self.assertEqual(add_business_days(TUE, 3), FRI); self.assertEqual(add_business_days(TUE, 4), MON)
        self.assertEqual(add_business_days(FRI, 1), MON); self.assertEqual(add_business_days(SAT, 1), MON)

    def test_add_zero(self):
        self.assertEqual(add_business_days(TUE, 0), TUE); self.assertEqual(add_business_days(SAT, 0), MON)
        self.assertEqual(add_business_days(FRI, 0, {FRI}), MON)

    def test_add_backward(self):
        self.assertEqual(add_business_days(MON, -1), FRI); self.assertEqual(add_business_days(SUN, -1), FRI)
        self.assertEqual(add_business_days(MON, -5), date(2026, 10, 5))

    def test_holidays(self):
        self.assertEqual(add_business_days(FRI, 1, {MON}), date(2026, 10, 13))
        self.assertEqual(add_business_days(date(2026, 10, 13), -1, [MON]), FRI)
        self.assertEqual(add_business_days(FRI, 1, (MON,)), date(2026, 10, 13))

    def test_between(self):
        self.assertEqual(business_days_between(MON, date(2026, 10, 19)), 5)
        self.assertEqual(business_days_between(TUE, TUE), 0); self.assertEqual(business_days_between(TUE, date(2026, 10, 7)), 1)
        self.assertEqual(business_days_between(date(2026, 10, 19), MON), -5)
        self.assertEqual(business_days_between(MON, date(2026, 10, 19), [date(2026, 10, 14)]), 4)
        self.assertEqual(business_days_between(SAT, MON), 0)

    def test_next(self):
        self.assertEqual(next_business_day(FRI), MON); self.assertEqual(next_business_day(FRI, [MON]), date(2026, 10, 13))
        self.assertEqual(next_business_day(TUE), date(2026, 10, 7))

    def test_consistency(self):
        hol = [date(2026, 12, 25), date(2027, 1, 1)]
        for n in range(-40, 41):
            d = add_business_days(TUE, n, hol)
            self.assertTrue(is_business_day(d, hol))
            self.assertEqual(business_days_between(TUE, d, hol), n)
'''))

# ---------------------------------------------------------------- 17
TASKS.append(dict(
id="17_async_pool", difficulty="medium",
prompt=r'''Create `apool.py` with:

`async def run_limited(funcs, limit, *, return_exceptions=False, timeout=None) -> list`
- `funcs`: an iterable (possibly a generator) of zero-argument callables, each returning an awaitable.
- Run them with at most `limit` in flight at any moment. Call each callable lazily — only when a slot is free.
- Return results in INPUT order.
- If a call raises and `return_exceptions` is False: stop starting new calls, cancel the ones still running (and let them finish
  cancelling), then re-raise that exception. If `return_exceptions` is True, place the exception object in the results list instead.
- `timeout`: optional per-call timeout in seconds; a timed-out call counts as raising `asyncio.TimeoutError`.
- `limit < 1` raises `ValueError`. An empty input returns `[]`.
Python 3.10, stdlib only.
''',
starter={},
ref={"apool.py": r'''import asyncio


async def run_limited(funcs, limit, *, return_exceptions=False, timeout=None):
    if limit < 1:
        raise ValueError("limit must be >= 1")
    funcs = list(funcs)
    results = [None] * len(funcs)
    it = iter(enumerate(funcs))

    async def call(f):
        aw = f()
        if timeout is not None:
            return await asyncio.wait_for(aw, timeout)
        return await aw

    async def worker():
        for i, f in it:
            try:
                results[i] = await call(f)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                if return_exceptions:
                    results[i] = e
                else:
                    raise

    workers = [asyncio.ensure_future(worker()) for _ in range(min(limit, len(funcs)))]
    if not workers:
        return []
    try:
        done, _ = await asyncio.wait(workers, return_when=asyncio.FIRST_EXCEPTION)
        for w in done:
            if not w.cancelled() and w.exception() is not None:
                raise w.exception()
    finally:
        for w in workers:
            if not w.done():
                w.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
    return results
'''},
tests=r'''import asyncio, unittest, time
from apool import run_limited


class T(unittest.IsolatedAsyncioTestCase):
    async def test_order_and_limit(self):
        running = 0; peak = 0
        def mk(i):
            async def f():
                nonlocal running, peak
                running += 1; peak = max(peak, running)
                await asyncio.sleep(0.01 * (3 - i % 3))
                running -= 1
                return i * i
            return f
        res = await run_limited([mk(i) for i in range(20)], 4)
        self.assertEqual(res, [i * i for i in range(20)]); self.assertEqual(peak, 4)

    async def test_parallel_speed(self):
        t = time.perf_counter()
        await run_limited([lambda: asyncio.sleep(0.2) for _ in range(10)], 10)
        self.assertLess(time.perf_counter() - t, 0.6)

    async def test_lazy(self):
        calls = []; gate = asyncio.Event()
        def mk(i):
            def f():
                calls.append(i)
                async def body():
                    await gate.wait(); return i
                return body()
            return f
        task = asyncio.ensure_future(run_limited([mk(i) for i in range(10)], 3))
        await asyncio.sleep(0.05)
        self.assertEqual(len(calls), 3)
        gate.set(); self.assertEqual(await task, list(range(10)))

    async def test_error_cancels(self):
        cancelled = []; started = []
        def mk(i):
            async def f():
                started.append(i)
                try:
                    if i == 2:
                        await asyncio.sleep(0.05); raise KeyError('boom')
                    await asyncio.sleep(2); return i
                except asyncio.CancelledError:
                    cancelled.append(i); raise
            return f
        t = time.perf_counter()
        with self.assertRaises(KeyError): await run_limited([mk(i) for i in range(10)], 3)
        self.assertLess(time.perf_counter() - t, 1.0)
        await asyncio.sleep(0.05)
        self.assertEqual(sorted(cancelled), [0, 1]); self.assertEqual(sorted(started), [0, 1, 2])

    async def test_return_exceptions(self):
        async def ok(v): return v
        async def bad(): raise ValueError("x")
        res = await run_limited([lambda: ok(1), bad, lambda: ok(3)], 2, return_exceptions=True)
        self.assertEqual(res[0], 1); self.assertIsInstance(res[1], ValueError); self.assertEqual(res[2], 3)

    async def test_timeout(self):
        res = await run_limited([lambda: asyncio.sleep(1), lambda: asyncio.sleep(0, result=5)], 2, timeout=0.1, return_exceptions=True)
        self.assertIsInstance(res[0], asyncio.TimeoutError); self.assertEqual(res[1], 5)

    async def test_timeout_raises(self):
        with self.assertRaises(asyncio.TimeoutError):
            await run_limited([lambda: asyncio.sleep(1)], 1, timeout=0.05)

    async def test_validation_and_empty(self):
        with self.assertRaises(ValueError): await run_limited([], 0)
        self.assertEqual(await run_limited([], 3), [])

    async def test_generator_input(self):
        async def sq(i): return i * i
        res = await run_limited((lambda i=i: sq(i) for i in range(7)), 2)
        self.assertEqual(res, [i * i for i in range(7)])
'''))

# ---------------------------------------------------------------- 18
TASKS.append(dict(
id="18_kv_transactions", difficulty="easy",
prompt=r'''Create `kvstore.py` with an in-memory key-value store supporting nested transactions.

- Exception class `NoTransaction(Exception)`.
- `KVStore()` with methods:
  * `set(key, value)` (values are hashable), `get(key)` -> value or `None` if missing, `delete(key)` -> True if the key existed else False.
  * `count(value)` -> number of keys currently holding `value`. It will be called extremely often on stores with hundreds of
    thousands of keys, so it must be O(1) (do not scan all keys).
  * `begin()` opens a (possibly nested) transaction.
  * `rollback()` undoes all changes made since the most recent `begin()` and closes that transaction; raises `NoTransaction` if none is open.
  * `commit()` makes all changes permanent and closes ALL open transactions; raises `NoTransaction` if none is open.
''',
starter={},
ref={"kvstore.py": r'''class NoTransaction(Exception):
    pass


_MISSING = object()


class KVStore:
    def __init__(self):
        self._data, self._counts, self._tx = {}, {}, []

    def _raw(self, k, v):
        old = self._data.get(k, _MISSING)
        if old is not _MISSING:
            c = self._counts[old] - 1
            if c: self._counts[old] = c
            else: del self._counts[old]
        if v is _MISSING:
            self._data.pop(k, None)
        else:
            self._data[k] = v
            self._counts[v] = self._counts.get(v, 0) + 1
        return old

    def _log(self, k, old):
        if self._tx and k not in self._tx[-1]:
            self._tx[-1][k] = old

    def set(self, k, v):
        self._log(k, self._raw(k, v))

    def get(self, k):
        return self._data.get(k)

    def delete(self, k):
        if k not in self._data:
            return False
        self._log(k, self._raw(k, _MISSING))
        return True

    def count(self, v):
        return self._counts.get(v, 0)

    def begin(self):
        self._tx.append({})

    def rollback(self):
        if not self._tx:
            raise NoTransaction()
        for k, old in self._tx.pop().items():
            self._raw(k, old)

    def commit(self):
        if not self._tx:
            raise NoTransaction()
        self._tx.clear()
'''},
tests=r'''import unittest, time
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
'''))

# ---------------------------------------------------------------- 19
TASKS.append(dict(
id="19_regex_engine", difficulty="hard",
prompt=r'''Create `rematch.py`, a small regular-expression engine. Do NOT import or use the `re` module.

- `fullmatch(pattern, text) -> bool`: the whole text must match.
- `search(pattern, text) -> bool`: some substring matches.

Pattern syntax:
- Literal characters; `.` matches any single character.
- Character classes `[abc]`, ranges `[a-z0-9]`, negated `[^...]`. Inside a class `\` escapes the next character.
- `\` outside a class makes the next character literal (e.g. `\.`, `\*`, `\[`, `\\`).
- Quantifiers `*`, `+`, `?` apply to the single preceding atom (char, `.`, or class). No groups or alternation.
- In `search`, a leading `^` anchors to the start and a trailing `$` anchors to the end of text. (`fullmatch` accepts them too, with no effect.)
- Invalid patterns raise `ValueError`: a quantifier with nothing to repeat (`*a`, `+`), stacked quantifiers (`a**`, `a+?`, `a?*`),
  an unterminated class (`[abc`), a reversed range (`[z-a]`), or a trailing lone backslash.
- Must not blow up exponentially: e.g. `fullmatch("a*a*a*a*a*a*a*a*b", "a" * 40)` must return False quickly.
''',
starter={},
ref={"rematch.py": r'''import sys
from functools import lru_cache

sys.setrecursionlimit(max(sys.getrecursionlimit(), 20000))


def _compile(p):
    toks, i, n = [], 0, len(p)
    while i < n:
        c = p[i]
        if c in '*+?':
            if not toks or toks[-1][1] != '1':
                raise ValueError("nothing to repeat at %d" % i)
            toks[-1] = (toks[-1][0], c)
            i += 1
            continue
        if c == '\\':
            if i + 1 >= n:
                raise ValueError("trailing backslash")
            toks.append((('lit', p[i + 1]), '1')); i += 2; continue
        if c == '[':
            j, neg, items, first = i + 1, False, [], True
            if j < n and p[j] == '^':
                neg = True; j += 1
            while True:
                if j >= n:
                    raise ValueError("unterminated class")
                ch = p[j]
                if ch == ']' and not first:
                    break
                if ch == '\\':
                    if j + 1 >= n:
                        raise ValueError("unterminated class")
                    ch = p[j + 1]; j += 2
                else:
                    j += 1
                if j + 1 < n and p[j] == '-' and p[j + 1] != ']':
                    hi = p[j + 1]; j += 2
                    if hi == '\\':
                        if j >= n:
                            raise ValueError("unterminated class")
                        hi = p[j]; j += 1
                    if hi < ch:
                        raise ValueError("bad range")
                    items.append((ch, hi))
                else:
                    items.append((ch, ch))
                first = False
            toks.append((('cls', neg, tuple(items)), '1')); i = j + 1; continue
        if c == '.':
            toks.append((('any',), '1')); i += 1; continue
        toks.append((('lit', c), '1')); i += 1
    out = []
    for mt, q in toks:
        if q == '+':
            out.append((mt, '1')); out.append((mt, '*'))
        else:
            out.append((mt, q))
    return out


def _ok(mt, ch):
    if mt[0] == 'any': return True
    if mt[0] == 'lit': return mt[1] == ch
    hit = any(a <= ch <= b for a, b in mt[2])
    return hit != mt[1]


def _strip(p):
    a = p.startswith('^')
    if a: p = p[1:]
    z = False
    if p.endswith('$'):
        k = len(p) - 1; bs = 0
        while k - 1 - bs >= 0 and p[k - 1 - bs] == '\\': bs += 1
        if bs % 2 == 0:
            z = True; p = p[:-1]
    return p, a, z


def _matcher(toks, text, must_end):
    n, T = len(text), len(toks)

    @lru_cache(maxsize=None)
    def m(ti, si):
        if ti == T:
            return si == n if must_end else True
        mt, q = toks[ti]
        if q == '1':
            return si < n and _ok(mt, text[si]) and m(ti + 1, si + 1)
        if q == '?':
            return m(ti + 1, si) or (si < n and _ok(mt, text[si]) and m(ti + 1, si + 1))
        return m(ti + 1, si) or (si < n and _ok(mt, text[si]) and m(ti, si + 1))
    return m


def fullmatch(pattern, text):
    p, _, _ = _strip(pattern)
    return _matcher(tuple(_compile(p)), text, True)(0, 0)


def search(pattern, text):
    p, a, z = _strip(pattern)
    m = _matcher(tuple(_compile(p)), text, z)
    starts = [0] if a else range(len(text) + 1)
    return any(m(0, s) for s in starts)
'''},
tests=r'''import unittest, random, time, pathlib
import re as pyre
from rematch import fullmatch, search


class T(unittest.TestCase):
    def test_basic(self):
        self.assertTrue(fullmatch("abc", "abc")); self.assertFalse(fullmatch("abc", "abcd")); self.assertTrue(fullmatch("a.c", "axc"))
        self.assertTrue(fullmatch("ab*c", "ac")); self.assertTrue(fullmatch("ab+c", "abbbc")); self.assertFalse(fullmatch("ab+c", "ac"))
        self.assertTrue(fullmatch("colou?r", "color")); self.assertTrue(fullmatch("", ""))

    def test_classes(self):
        self.assertTrue(fullmatch("[a-c]+", "abcabc")); self.assertFalse(fullmatch("[a-c]+", "abd"))
        self.assertTrue(fullmatch("[^0-9]*", "abc")); self.assertFalse(fullmatch("[^0-9]*", "ab1"))
        self.assertTrue(fullmatch("[a-z0-9_]+", "var_1")); self.assertTrue(fullmatch(r"[\]x]+", "]x]")); self.assertTrue(fullmatch(r"[\-a]", "-"))

    def test_escapes(self):
        self.assertTrue(fullmatch(r"a\.b", "a.b")); self.assertFalse(fullmatch(r"a\.b", "axb")); self.assertTrue(fullmatch(r"\*+", "***"))
        self.assertTrue(fullmatch(r"\[x\]", "[x]")); self.assertTrue(fullmatch(r"a\\b", "a\\b"))

    def test_search_anchors(self):
        self.assertTrue(search("b+c", "aabbcd")); self.assertFalse(search("^b", "ab")); self.assertTrue(search("^a", "ab"))
        self.assertTrue(search("b$", "ab")); self.assertFalse(search("a$", "ab")); self.assertTrue(search("^ab$", "ab"))
        self.assertTrue(search("x*", "")); self.assertTrue(search(r"\$", "a$b")); self.assertTrue(search("", "abc"))

    def test_invalid(self):
        for p in ["*a", "+", "a**", "a+?", "a?*", "[abc", "[z-a]", "a\\", "[]"]:
            with self.subTest(p=p):
                with self.assertRaises(ValueError): fullmatch(p, "a")

    def test_random_vs_re(self):
        rnd = random.Random(9)
        atoms = ['a', 'b', '.', '[ab]', '[^a]', '[a-b]', 'c']
        for _ in range(1500):
            p = ''.join(rnd.choice(atoms) + rnd.choice(['', '', '*', '+', '?']) for _ in range(rnd.randint(1, 5)))
            for _ in range(4):
                t = ''.join(rnd.choice('abc') for _ in range(rnd.randint(0, 8)))
                self.assertEqual(fullmatch(p, t), pyre.fullmatch(p, t) is not None, (p, t))
                self.assertEqual(search(p, t), pyre.search(p, t) is not None, (p, t))

    def test_pathological(self):
        t = time.perf_counter()
        self.assertFalse(fullmatch("a*a*a*a*a*a*a*a*b", "a" * 40))
        self.assertFalse(search("a*a*a*a*a*a*b", "a" * 60))
        self.assertTrue(fullmatch(".*.*.*x", "y" * 200 + "x"))
        self.assertLess(time.perf_counter() - t, 3.0)

    def test_no_re(self):
        src = pathlib.Path(__import__('rematch').__file__).read_text(encoding="utf-8")
        self.assertNotIn("import re\n", src + "\n"); self.assertNotIn("from re ", src); self.assertNotIn("import re,", src)
'''))

# ---------------------------------------------------------------- 20
TASKS.append(dict(
id="20_dependency_resolver", difficulty="medium",
prompt=r'''Create `deps.py` for a build system's dependency resolution.

Input `deps: dict[str, Iterable[str]]` maps each target to the targets it depends on (dependencies must be built first).
Nodes that only appear as dependencies are part of the graph too. Duplicate dependencies are allowed.

- Exception `CycleError(ValueError)` with attribute `cycle`: a list `[n0, n1, ..., nk, n0]` where each consecutive pair (x, y)
  means x depends on y (a self-dependency gives `['a', 'a']`).
- `build_order(deps) -> list[str]`: a valid build order containing every node; whenever several nodes are ready, pick the
  lexicographically smallest (so the result is deterministic). Raise `CycleError` if there is a cycle.
- `layers(deps) -> list[list[str]]`: layer 0 = nodes with no dependencies; a node is in layer k if its deepest dependency is in
  layer k-1. Each layer sorted. Raise `CycleError` on cycles.
- `affected(deps, changed) -> set[str]`: the changed nodes plus every node that transitively depends on any of them.
- Must handle graphs with 10,000+ nodes and dependency chains thousands of nodes deep (including long cycles) without hitting
  Python's recursion limit.
''',
starter={},
ref={"deps.py": r'''import heapq


class CycleError(ValueError):
    def __init__(self, cycle):
        super().__init__("cycle: " + " -> ".join(cycle))
        self.cycle = cycle


def _graph(deps):
    g = {}
    for k, vs in deps.items():
        g.setdefault(k, set())
        for v in vs:
            g[k].add(v); g.setdefault(v, set())
    return g


def _find_cycle(g, nodes):
    color = {}
    for start in sorted(nodes):
        if color.get(start):
            continue
        stack = [(start, iter(sorted(g[start])))]; path = [start]; color[start] = 1
        while stack:
            u, it = stack[-1]
            nxt = next(it, None)
            if nxt is None:
                stack.pop(); path.pop(); color[u] = 2; continue
            if nxt not in nodes:
                continue
            c = color.get(nxt)
            if c == 1:
                i = path.index(nxt); return path[i:] + [nxt]
            if c is None:
                color[nxt] = 1; path.append(nxt); stack.append((nxt, iter(sorted(g[nxt]))))
    return None


def _kahn(deps):
    g = _graph(deps)
    rdeps = {n: [] for n in g}
    indeg = {n: len(g[n]) for n in g}
    for n, ds in g.items():
        for d in ds:
            rdeps[d].append(n)
    return g, rdeps, indeg


def build_order(deps):
    g, rdeps, indeg = _kahn(deps)
    ready = [n for n, d in indeg.items() if d == 0]; heapq.heapify(ready)
    out = []
    while ready:
        n = heapq.heappop(ready); out.append(n)
        for m in rdeps[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                heapq.heappush(ready, m)
    if len(out) != len(g):
        raise CycleError(_find_cycle(g, {n for n in g if indeg[n] > 0}))
    return out


def layers(deps):
    g, rdeps, indeg = _kahn(deps)
    cur = sorted(n for n, d in indeg.items() if d == 0); out = []; seen = 0
    while cur:
        out.append(cur); seen += len(cur); nxt = []
        for n in cur:
            for m in rdeps[n]:
                indeg[m] -= 1
                if indeg[m] == 0:
                    nxt.append(m)
        cur = sorted(nxt)
    if seen != len(g):
        raise CycleError(_find_cycle(g, {n for n in g if indeg[n] > 0}))
    return out


def affected(deps, changed):
    g, rdeps, _ = _kahn(deps)
    res = set(changed); stack = list(res)
    while stack:
        n = stack.pop()
        for m in rdeps.get(n, ()):
            if m not in res:
                res.add(m); stack.append(m)
    return res
'''},
tests=r'''import unittest, random
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
'''))
