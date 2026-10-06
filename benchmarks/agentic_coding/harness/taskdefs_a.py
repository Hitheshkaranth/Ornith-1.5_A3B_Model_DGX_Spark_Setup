TASKS = []

# ---------------------------------------------------------------- 01
TASKS.append(dict(
id="01_lru_ttl", difficulty="easy",
prompt=r'''Implement `lru_cache.py` containing class `LRUCache`:

- `LRUCache(capacity: int, ttl: float | None = None, clock=time.monotonic)`. `capacity < 1` raises `ValueError`.
- `put(key, value)`: insert or update. Updating an existing key refreshes its recency AND resets its TTL timer.
  When inserting a NEW key into a full cache, first drop all expired entries; if still full, evict the least-recently-used entry.
- `get(key, default=None)`: return the value if present and not expired (and mark it most-recently-used); otherwise return `default`.
- An entry is expired when `clock() - time_it_was_inserted_or_last_updated >= ttl`. `ttl=None` means never expire.
- `__len__`: number of non-expired entries. `__contains__(key)`: True if present and not expired; it must NOT change recency.
- `keys()`: list of non-expired keys ordered from least- to most-recently used.
''',
starter={"lru_cache.py": "# Implement LRUCache here.\n"},
ref={"lru_cache.py": r'''import time
from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity, ttl=None, clock=time.monotonic):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity, self.ttl, self.clock = capacity, ttl, clock
        self._d = OrderedDict()

    def _expired(self, t):
        return self.ttl is not None and self.clock() - t >= self.ttl

    def _purge(self):
        for k in [k for k, (_, t) in self._d.items() if self._expired(t)]:
            del self._d[k]

    def put(self, key, value):
        if key in self._d:
            self._d[key] = (value, self.clock())
            self._d.move_to_end(key)
            return
        if len(self._d) >= self.capacity:
            self._purge()
            if len(self._d) >= self.capacity:
                self._d.popitem(last=False)
        self._d[key] = (value, self.clock())

    def get(self, key, default=None):
        if key not in self._d:
            return default
        v, t = self._d[key]
        if self._expired(t):
            del self._d[key]
            return default
        self._d.move_to_end(key)
        return v

    def __contains__(self, key):
        return key in self._d and not self._expired(self._d[key][1])

    def __len__(self):
        return sum(1 for _, t in self._d.values() if not self._expired(t))

    def keys(self):
        return [k for k, (_, t) in self._d.items() if not self._expired(t)]
'''},
tests=r'''import unittest
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
'''))

# ---------------------------------------------------------------- 02
TASKS.append(dict(
id="02_intervals_bugfix", difficulty="medium",
prompt=r'''Users report wrong results from `intervals.py`. Find and fix all the bugs. Required behaviour:

- Intervals are `[start, end]` pairs (lists or tuples) of numbers with `start <= end`. Any interval with `start > end` raises `ValueError`.
- `merge_intervals(intervals)`: input may be in any order. Overlapping OR touching intervals (`[1,3]` and `[3,5]`) are merged.
  Returns a NEW list of `[start, end]` lists sorted by start. It must never mutate its input (nor the inner lists).
- `insert_interval(intervals, new)`: `intervals` may be unsorted/overlapping. Returns exactly what `merge_intervals(intervals + [new])` would. Must not mutate inputs.
- `total_covered(intervals)`: total length of the union of the intervals (overlaps counted once).
- Empty input: `merge_intervals([]) == []`, `total_covered([]) == 0`.
''',
starter={"intervals.py": r'''def merge_intervals(intervals):
    """Merge overlapping or touching closed intervals [start, end]."""
    result = []
    for iv in intervals:
        if result and iv[0] < result[-1][1]:
            result[-1][1] = max(result[-1][1], iv[1])
        else:
            result.append(iv)
    return result


def insert_interval(intervals, new):
    """Insert `new` into a list of intervals and merge."""
    out = []
    i = 0
    while i < len(intervals) and intervals[i][1] < new[0]:
        out.append(intervals[i])
        i += 1
    while i < len(intervals) and intervals[i][0] <= new[1]:
        new = [min(new[0], intervals[i][0]), max(new[1], intervals[i][1])]
        i += 1
    out.append(new)
    return out


def total_covered(intervals):
    """Total length covered by the union of the intervals."""
    return sum(e - s for s, e in intervals)
'''},
ref={"intervals.py": r'''def merge_intervals(intervals):
    ivs = []
    for s, e in intervals:
        if s > e:
            raise ValueError("start > end")
        ivs.append([s, e])
    ivs.sort()
    out = []
    for s, e in ivs:
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out


def insert_interval(intervals, new):
    return merge_intervals(list(intervals) + [new])


def total_covered(intervals):
    return sum(e - s for s, e in merge_intervals(intervals))
'''},
tests=r'''import unittest, copy
from intervals import merge_intervals, insert_interval, total_covered


class T(unittest.TestCase):
    def test_basic(self): self.assertEqual(merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]), [[1, 6], [8, 10], [15, 18]])
    def test_unsorted(self): self.assertEqual(merge_intervals([[8, 10], [1, 3], [2, 6]]), [[1, 6], [8, 10]])
    def test_touching(self): self.assertEqual(merge_intervals([[1, 3], [3, 5]]), [[1, 5]])
    def test_contained(self): self.assertEqual(merge_intervals([[1, 10], [2, 3], [4, 5]]), [[1, 10]])

    def test_no_mutation(self):
        data = [[1, 3], [2, 6]]; snap = copy.deepcopy(data); merge_intervals(data); self.assertEqual(data, snap)

    def test_result_not_aliased(self):
        data = [[1, 3]]; out = merge_intervals(data); out[0][1] = 99; self.assertEqual(data, [[1, 3]])

    def test_tuples_input(self): self.assertEqual(merge_intervals([(5, 6), (1, 2)]), [[1, 2], [5, 6]])

    def test_empty(self):
        self.assertEqual(merge_intervals([]), []); self.assertEqual(total_covered([]), 0)

    def test_invalid(self):
        with self.assertRaises(ValueError): merge_intervals([[3, 1]])

    def test_insert_middle(self):
        self.assertEqual(insert_interval([[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8]), [[1, 2], [3, 10], [12, 16]])

    def test_insert_keeps_tail(self): self.assertEqual(insert_interval([[1, 2], [10, 12]], [4, 5]), [[1, 2], [4, 5], [10, 12]])
    def test_insert_unsorted(self): self.assertEqual(insert_interval([[10, 12], [1, 2]], [2, 4]), [[1, 4], [10, 12]])

    def test_insert_no_mutation(self):
        data = [[1, 2], [5, 6]]; insert_interval(data, [2, 5]); self.assertEqual(data, [[1, 2], [5, 6]])

    def test_total(self): self.assertEqual(total_covered([[1, 3], [2, 6], [10, 11]]), 6)
    def test_total_float(self): self.assertAlmostEqual(total_covered([[0.5, 1.5], [1.0, 2.0]]), 1.5)
'''))

# ---------------------------------------------------------------- 03
TASKS.append(dict(
id="03_expr_evaluator", difficulty="hard",
prompt=r'''Create `calc.py` with `evaluate(expr: str)` and exception class `CalcError` (a subclass of `ValueError`).

`evaluate` parses and computes an arithmetic expression and returns a number (int or float, compared with tolerance).
You MUST write your own tokenizer/parser: do not use `eval`, `exec`, `compile` or the `ast` module.

Grammar / semantics:
- Numbers: digits with at most one decimal point, at least one digit (`12`, `1.5`, `.5`, `5.` are valid; `1..2` and `.` are not).
- Binary operators: `+ - * / % **`. `/` is true division, `%` follows Python semantics.
- Precedence (high to low): `**` (right-associative), unary `+`/`-`, then `* / %` (left-assoc), then `+ -` (left-assoc).
  So `-2**2 == -4`, `2**3**2 == 512`, `2**-1 == 0.5`, `3*-2 == -6`, `--3 == 3`.
- Parentheses for grouping. Whitespace (spaces, tabs) is ignored.
- Raise `CalcError` for: empty input, unknown characters, malformed numbers, unbalanced parentheses, missing operands,
  two operands without an operator (`2 3`, `2(3)` — there is no implicit multiplication), and division or modulo by zero.
''',
starter={},
ref={"calc.py": r'''class CalcError(ValueError):
    pass


def _tokenize(s):
    toks, i = [], 0
    while i < len(s):
        c = s[i]
        if c.isspace():
            i += 1; continue
        if c.isdigit() or c == '.':
            j, dots = i, 0
            while j < len(s) and (s[j].isdigit() or s[j] == '.'):
                dots += s[j] == '.'; j += 1
            txt = s[i:j]
            if dots > 1 or txt == '.':
                raise CalcError("bad number %r" % txt)
            toks.append(('num', float(txt) if dots else int(txt))); i = j; continue
        if s.startswith('**', i):
            toks.append(('op', '**')); i += 2; continue
        if c in '+-*/%()':
            toks.append(('op', c)); i += 1; continue
        raise CalcError("unexpected %r" % c)
    return toks


class _P:
    def __init__(s, t): s.t, s.i = t, 0
    def peek(s): return s.t[s.i] if s.i < len(s.t) else (None, None)
    def take(s): tok = s.peek(); s.i += 1; return tok
    def isop(s, *ops): k, v = s.peek(); return k == 'op' and v in ops

    def expr(s):
        v = s.term()
        while s.isop('+', '-'):
            op = s.take()[1]; r = s.term(); v = v + r if op == '+' else v - r
        return v

    def term(s):
        v = s.unary()
        while s.isop('*', '/', '%'):
            op = s.take()[1]; r = s.unary()
            if op == '*':
                v = v * r
            else:
                if r == 0: raise CalcError("division by zero")
                v = v / r if op == '/' else v % r
        return v

    def unary(s):
        if s.isop('+', '-'):
            op = s.take()[1]; v = s.unary(); return -v if op == '-' else v
        return s.power()

    def power(s):
        b = s.atom()
        if s.isop('**'):
            s.take(); e = s.unary()
            try:
                return b ** e
            except ZeroDivisionError:
                raise CalcError("division by zero")
        return b

    def atom(s):
        k, v = s.take()
        if k == 'num': return v
        if (k, v) == ('op', '('):
            r = s.expr()
            if s.take() != ('op', ')'): raise CalcError("expected )")
            return r
        raise CalcError("unexpected token")


def evaluate(expr):
    p = _P(_tokenize(expr))
    if not p.t: raise CalcError("empty")
    v = p.expr()
    if p.i != len(p.t): raise CalcError("trailing input")
    return v
'''},
tests=r'''import unittest, pathlib
from calc import evaluate, CalcError


class T(unittest.TestCase):
    def ok(self, e, v): self.assertAlmostEqual(evaluate(e), v, places=9, msg=e)

    def test_basic(self): self.ok("1+2", 3); self.ok("2*3+4", 10); self.ok("2+3*4", 14); self.ok("10-4-3", 3)
    def test_div(self): self.ok("7/2", 3.5); self.ok("8/2/2", 2); self.ok("7%3", 1); self.ok("-7%3", 2)
    def test_parens(self): self.ok("(2+3)*4", 20); self.ok("((1))", 1); self.ok("2*(3+(4-1))*2", 24)
    def test_unary(self):
        self.ok("-3", -3); self.ok("--3", 3); self.ok("-(2+3)", -5); self.ok("+4", 4); self.ok("3*-2", -6); self.ok("1 - -1", 2)
    def test_power(self): self.ok("2**3", 8); self.ok("2**3**2", 512); self.ok("-2**2", -4); self.ok("2**-1", 0.5); self.ok("(-2)**2", 4)
    def test_decimals(self): self.ok("1.5*2", 3); self.ok(".5+.5", 1); self.ok("5.+1", 6)
    def test_whitespace(self): self.ok("  1 +\t2  ", 3)

    def test_errors(self):
        for e in ["", "   ", "1+", "(1+2", "1+2)", "2 3", "1..2", "abc", "2(3)", "*2", "1/0", "5%0", ")(", "1 +* 2", "."]:
            with self.subTest(e=e):
                with self.assertRaises(CalcError): evaluate(e)

    def test_calcerror_is_valueerror(self): self.assertTrue(issubclass(CalcError, ValueError))

    def test_no_eval(self):
        src = pathlib.Path(__import__('calc').__file__).read_text(encoding="utf-8")
        for bad in ["eval(", "exec(", "compile(", "import ast", "from ast"]:
            self.assertNotIn(bad, src)
'''))

# ---------------------------------------------------------------- 04
TASKS.append(dict(
id="04_csv_parser", difficulty="medium",
prompt=r'''Create `csvparse.py` with two functions. Do NOT use the `csv` module.

`parse_csv(text: str, delimiter: str = ",") -> list[list[str]]`
- Records are separated by `\n` or `\r\n`. A single trailing line break at the end of the input does not create an extra record. Empty input returns `[]`.
- Fields are separated by `delimiter`. A field may be enclosed in double quotes; inside quotes `""` is a literal `"`, and delimiters and line breaks are literal text.
- After a closing quote the next character must be the delimiter, a line break, or end of input; otherwise raise `ValueError`.
- A `"` appearing inside an unquoted field (not at its start) is a literal character (`ab"c` -> `ab"c`).
- An unterminated quoted field raises `ValueError`.
- An empty line produces the record `['']`.

`to_csv(rows, delimiter=",") -> str`
- Quote a field (doubling inner quotes) iff it contains the delimiter, `"`, `\r` or `\n`.
- Each row is terminated by `\r\n` (including the last one).
- `parse_csv(to_csv(rows)) == rows` must hold for any list of rows of strings (each row with at least one field).
''',
starter={},
ref={"csvparse.py": r'''def parse_csv(text, delimiter=","):
    if not text:
        return []
    rows, row, field = [], [], []
    i, n = 0, len(text)
    in_q = after_q = False
    while i < n:
        c = text[i]
        if in_q:
            if c == '"':
                if i + 1 < n and text[i + 1] == '"':
                    field.append('"'); i += 2; continue
                in_q, after_q = False, True; i += 1; continue
            field.append(c); i += 1; continue
        if c == delimiter:
            row.append(''.join(field)); field = []; after_q = False; i += 1; continue
        if c == '\n' or (c == '\r' and i + 1 < n and text[i + 1] == '\n'):
            row.append(''.join(field)); rows.append(row); row, field = [], []; after_q = False
            i += 2 if c == '\r' else 1; continue
        if after_q:
            raise ValueError("unexpected character after closing quote at %d" % i)
        if c == '"' and not field:
            in_q = True; i += 1; continue
        field.append(c); i += 1
    if in_q:
        raise ValueError("unterminated quoted field")
    if not text.endswith('\n'):
        row.append(''.join(field)); rows.append(row)
    return rows


def to_csv(rows, delimiter=","):
    out = []
    for r in rows:
        cells = []
        for f in r:
            f = str(f)
            if any(ch in f for ch in (delimiter, '"', '\r', '\n')):
                f = '"' + f.replace('"', '""') + '"'
            cells.append(f)
        out.append(delimiter.join(cells) + "\r\n")
    return ''.join(out)
'''},
tests=r'''import unittest, pathlib, random
from csvparse import parse_csv, to_csv


class T(unittest.TestCase):
    def test_simple(self): self.assertEqual(parse_csv("a,b,c\n1,2,3\n"), [['a', 'b', 'c'], ['1', '2', '3']])
    def test_no_trailing_newline(self): self.assertEqual(parse_csv("a,b\nc,d"), [['a', 'b'], ['c', 'd']])
    def test_crlf(self): self.assertEqual(parse_csv("a,b\r\nc,d\r\n"), [['a', 'b'], ['c', 'd']])
    def test_empty(self): self.assertEqual(parse_csv(""), [])
    def test_empty_fields(self): self.assertEqual(parse_csv(",a,,\n"), [['', 'a', '', '']])
    def test_quoted(self): self.assertEqual(parse_csv('"a,b",c\n'), [['a,b', 'c']])
    def test_escaped_quote(self): self.assertEqual(parse_csv('"he said ""hi""",x'), [['he said "hi"', 'x']])
    def test_newline_in_quotes(self): self.assertEqual(parse_csv('"line1\nline2",b\r\nc,d'), [['line1\nline2', 'b'], ['c', 'd']])
    def test_empty_quoted(self): self.assertEqual(parse_csv('"",a'), [['', 'a']])
    def test_blank_line(self): self.assertEqual(parse_csv("a\n\nb\n"), [['a'], [''], ['b']])
    def test_literal_quote_unquoted(self): self.assertEqual(parse_csv('ab"c,d'), [['ab"c', 'd']])
    def test_delimiter(self): self.assertEqual(parse_csv('a;"b;c";d', delimiter=';'), [['a', 'b;c', 'd']])

    def test_unterminated(self):
        with self.assertRaises(ValueError): parse_csv('"abc,d\n')

    def test_garbage_after_quote(self):
        with self.assertRaises(ValueError): parse_csv('"abc"x,d')

    def test_to_csv(self): self.assertEqual(to_csv([['a', 'b,c'], ['q"x', '']]), 'a,"b,c"\r\n"q""x",\r\n')

    def test_roundtrip(self):
        rnd = random.Random(7); alphabet = 'ab,"\n\r ;x'
        for _ in range(300):
            rows = [[''.join(rnd.choice(alphabet) for _ in range(rnd.randint(0, 6))) for _ in range(rnd.randint(1, 4))]
                    for _ in range(rnd.randint(1, 4))]
            self.assertEqual(parse_csv(to_csv(rows)), rows)

    def test_no_csv_module(self):
        src = pathlib.Path(__import__('csvparse').__file__).read_text(encoding="utf-8")
        self.assertNotIn('import csv', src); self.assertNotIn('from csv', src)
'''))

# ---------------------------------------------------------------- 05
TASKS.append(dict(
id="05_shop_multifile_bugfix", difficulty="medium",
prompt=r'''The `shop` package (shop/catalog.py, shop/pricing.py, shop/cart.py) has several bugs reported by finance and QA.
Fix the package so it satisfies this specification (keep the public API names):

Catalog
- `Catalog.add_product(sku, name, price, taxable=True)`: `price` is given as a str or Decimal and stored as `Decimal` (never float).
- `Catalog.get(sku)` returns the Product; unknown sku raises `KeyError`.

Cart(catalog)
- `add(sku, qty=1)`: qty must be a positive `int` (not bool/float) else `ValueError`; unknown sku -> `KeyError`.
  Adding an sku already in the cart increases that line's quantity (one line per sku).
- `remove(sku, qty=None)`: `None` removes the whole line; otherwise decrement and drop the line when it reaches 0.
  Removing more than is present raises `ValueError` (cart unchanged); sku not in cart raises `KeyError`.
- `lines()`: list of `(sku, qty)` tuples in first-insertion order.
- `subtotal()`: `Decimal` sum of price*qty (exact, unrounded).
- `total(coupon=None, tax_rate=Decimal("0"))` computes, with S = subtotal, T = subtotal of taxable lines:
    D   = coupon.discount(S)  (0 if no coupon)
    tax = T * (1 - D/S) * tax_rate     (0 when S == 0)   <- discount is applied BEFORE tax, proportionally
    total = S - D + tax
  and returns `total` rounded to cents with ROUND_HALF_UP as a Decimal with exactly 2 decimal places (e.g. `Decimal("0.00")`).

pricing
- `PercentCoupon(percent)`: requires 0 < percent <= 100 else `ValueError`; `discount(S) = S * percent / 100`.
- `FixedCoupon(amount)`: requires amount > 0 else `ValueError`; `discount(S) = min(amount, S)` (total never goes negative).
''',
starter={
"shop/__init__.py": "",
"shop/catalog.py": r'''from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Product:
    sku: str
    name: str
    price: Decimal
    taxable: bool = True


class Catalog:
    def __init__(self):
        self._products = {}

    def add_product(self, sku, name, price, taxable=True):
        self._products[sku] = Product(sku, name, float(price), taxable)

    def get(self, sku):
        return self._products.get(sku)
''',
"shop/pricing.py": r'''from decimal import Decimal, ROUND_HALF_UP


class PercentCoupon:
    def __init__(self, percent):
        self.percent = percent

    def discount(self, subtotal):
        return subtotal * self.percent / 100


class FixedCoupon:
    def __init__(self, amount):
        self.amount = amount

    def discount(self, subtotal):
        return self.amount


def round_money(x):
    return round(x, 2)
''',
"shop/cart.py": r'''from .pricing import round_money


class Cart:
    def __init__(self, catalog):
        self.catalog = catalog
        self._lines = []

    def add(self, sku, qty=1):
        product = self.catalog.get(sku)
        self._lines.append([sku, qty])

    def remove(self, sku, qty=None):
        for line in self._lines:
            if line[0] == sku:
                if qty is None:
                    self._lines.remove(line)
                else:
                    line[1] -= qty
                return

    def lines(self):
        return [tuple(l) for l in self._lines]

    def subtotal(self):
        return sum(self.catalog.get(s).price * q for s, q in self._lines)

    def total(self, coupon=None, tax_rate=0):
        sub = self.subtotal()
        taxable = sum(self.catalog.get(s).price * q for s, q in self._lines if self.catalog.get(s).taxable)
        tax = taxable * tax_rate
        total = sub + tax
        if coupon:
            total -= coupon.discount(total)
        return round_money(total)
'''},
ref={
"shop/__init__.py": "",
"shop/catalog.py": r'''from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Product:
    sku: str
    name: str
    price: Decimal
    taxable: bool = True


class Catalog:
    def __init__(self):
        self._products = {}

    def add_product(self, sku, name, price, taxable=True):
        self._products[sku] = Product(sku, name, Decimal(str(price)), taxable)

    def get(self, sku):
        return self._products[sku]
''',
"shop/pricing.py": r'''from decimal import Decimal, ROUND_HALF_UP


class PercentCoupon:
    def __init__(self, percent):
        percent = Decimal(str(percent))
        if not (0 < percent <= 100):
            raise ValueError("percent must be in (0, 100]")
        self.percent = percent

    def discount(self, subtotal):
        return subtotal * self.percent / 100


class FixedCoupon:
    def __init__(self, amount):
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError("amount must be > 0")
        self.amount = amount

    def discount(self, subtotal):
        return min(self.amount, subtotal)


def round_money(x):
    return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
''',
"shop/cart.py": r'''from decimal import Decimal
from .pricing import round_money


class Cart:
    def __init__(self, catalog):
        self.catalog = catalog
        self._lines = {}

    def add(self, sku, qty=1):
        if not isinstance(qty, int) or isinstance(qty, bool) or qty <= 0:
            raise ValueError("qty must be a positive int")
        self.catalog.get(sku)
        self._lines[sku] = self._lines.get(sku, 0) + qty

    def remove(self, sku, qty=None):
        if sku not in self._lines:
            raise KeyError(sku)
        if qty is None:
            del self._lines[sku]; return
        if qty > self._lines[sku]:
            raise ValueError("removing more than present")
        self._lines[sku] -= qty
        if self._lines[sku] == 0:
            del self._lines[sku]

    def lines(self):
        return list(self._lines.items())

    def subtotal(self):
        return sum((self.catalog.get(s).price * q for s, q in self._lines.items()), Decimal(0))

    def total(self, coupon=None, tax_rate=Decimal("0")):
        S = self.subtotal()
        T = sum((self.catalog.get(s).price * q for s, q in self._lines.items() if self.catalog.get(s).taxable), Decimal(0))
        D = coupon.discount(S) if coupon else Decimal(0)
        tax = T * (1 - D / S) * Decimal(str(tax_rate)) if S else Decimal(0)
        return round_money(S - D + tax)
'''},
tests=r'''import unittest
from decimal import Decimal as D
from shop.catalog import Catalog
from shop.cart import Cart
from shop.pricing import PercentCoupon, FixedCoupon


def mk():
    c = Catalog(); c.add_product('A', 'Apple', '0.10'); c.add_product('B', 'Book', '12.99', taxable=False)
    c.add_product('C', 'Cable', '5.555'); return c


class T(unittest.TestCase):
    def test_unknown_sku(self):
        c = mk()
        with self.assertRaises(KeyError): c.get('Z')
        with self.assertRaises(KeyError): Cart(c).add('Z')

    def test_add_merges(self):
        cart = Cart(mk()); cart.add('A', 2); cart.add('B'); cart.add('A', 3)
        self.assertEqual(cart.lines(), [('A', 5), ('B', 1)])

    def test_bad_qty(self):
        cart = Cart(mk())
        for q in (0, -1, 1.5, True):
            with self.assertRaises(ValueError): cart.add('A', q)

    def test_subtotal_decimal(self):
        cart = Cart(mk()); cart.add('A', 3); s = cart.subtotal(); self.assertIsInstance(s, D); self.assertEqual(s, D('0.30'))

    def test_remove(self):
        cart = Cart(mk()); cart.add('A', 3); cart.add('B', 1); cart.remove('A', 2)
        self.assertEqual(cart.lines(), [('A', 1), ('B', 1)])
        cart.remove('A', 1); self.assertEqual(cart.lines(), [('B', 1)]); cart.remove('B'); self.assertEqual(cart.lines(), [])

    def test_remove_errors(self):
        cart = Cart(mk()); cart.add('A', 1)
        with self.assertRaises(ValueError): cart.remove('A', 2)
        with self.assertRaises(KeyError): cart.remove('B')
        self.assertEqual(cart.lines(), [('A', 1)])

    def test_total_no_coupon(self):
        cart = Cart(mk()); cart.add('A', 3); cart.add('B', 1)
        self.assertEqual(cart.total(tax_rate=D('0.10')), D('13.32'))

    def test_total_returns_cents(self):
        cart = Cart(mk()); cart.add('C', 1); t = cart.total()
        self.assertEqual(t, D('5.56')); self.assertEqual(t.as_tuple().exponent, -2)

    def test_percent_before_tax(self):
        cart = Cart(mk()); cart.add('C', 2); cart.add('B', 1)
        self.assertEqual(cart.total(coupon=PercentCoupon(10), tax_rate=D('0.10')), D('22.69'))

    def test_fixed_coupon(self):
        cart = Cart(mk()); cart.add('C', 2); cart.add('B', 1)
        self.assertEqual(cart.total(coupon=FixedCoupon(D('5')), tax_rate=D('0.10')), D('19.98'))

    def test_fixed_capped(self):
        cart = Cart(mk()); cart.add('A', 1)
        self.assertEqual(cart.total(coupon=FixedCoupon(D('50')), tax_rate=D('0.2')), D('0.00'))

    def test_coupon_validation(self):
        for p in (0, -5, 101):
            with self.assertRaises(ValueError): PercentCoupon(p)
        with self.assertRaises(ValueError): FixedCoupon(D('0'))
        PercentCoupon(100)

    def test_rounding_half_up(self):
        c = Catalog(); c.add_product('X', 'x', '0.125'); cart = Cart(c); cart.add('X'); self.assertEqual(cart.total(), D('0.13'))

    def test_empty_cart(self):
        self.assertEqual(Cart(mk()).total(coupon=PercentCoupon(50), tax_rate=D('0.1')), D('0.00'))
'''))
