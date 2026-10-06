TASKS = []

# ---------------------------------------------------------------- 11
TASKS.append(dict(
id="11_calendar_slots", difficulty="medium",
prompt=r'''Create `calendar_slots.py` for finding meeting slots. Times are strings `"H:MM"` or `"HH:MM"` (hours 0-24, minutes 0-59;
`"24:00"` is allowed and means end of day; anything else such as `"24:30"`, `"7:5"`, `"ab:cd"` raises `ValueError`).
All returned times are zero-padded `"HH:MM"`.

- `free_slots(busy, day_start="09:00", day_end="17:00", min_minutes=30) -> list[tuple[str, str]]`
  `busy` is a list of `(start, end)` tuples; each must have start < end (else `ValueError`). Busy blocks may overlap, be unsorted,
  or extend outside the day (clip them). Return the free intervals inside `[day_start, day_end]`, sorted, each lasting at least
  `min_minutes`. Back-to-back busy blocks leave no gap.
- `common_free(calendars, day_start="09:00", day_end="17:00", min_minutes=30)`: `calendars` is a list of busy lists (one per
  person). Return intervals when EVERYONE is free (same rules/format as `free_slots`).
- `first_slot(calendars, duration, day_start="09:00", day_end="17:00")`: the earliest `(start, end)` of exactly `duration`
  minutes when everyone is free, or `None`.
''',
starter={},
ref={"calendar_slots.py": r'''import re

_T = re.compile(r'^(\d{1,2}):(\d{2})$')


def _m(s):
    m = _T.match(s) if isinstance(s, str) else None
    if not m:
        raise ValueError("bad time %r" % (s,))
    h, mi = int(m.group(1)), int(m.group(2))
    if mi > 59 or h > 24 or (h == 24 and mi != 0):
        raise ValueError("bad time %r" % (s,))
    return h * 60 + mi


def _f(x):
    return "%02d:%02d" % divmod(x, 60)


def _free(busy, ds, de, minm):
    blocks = []
    for s, e in busy:
        s, e = _m(s), _m(e)
        if s >= e:
            raise ValueError("start must be before end")
        s, e = max(s, ds), min(e, de)
        if s < e:
            blocks.append((s, e))
    blocks.sort()
    out, cur = [], ds
    for s, e in blocks:
        if s > cur and s - cur >= minm:
            out.append((cur, s))
        cur = max(cur, e)
    if de > cur and de - cur >= minm:
        out.append((cur, de))
    return out


def free_slots(busy, day_start="09:00", day_end="17:00", min_minutes=30):
    return [(_f(a), _f(b)) for a, b in _free(busy, _m(day_start), _m(day_end), min_minutes)]


def common_free(calendars, day_start="09:00", day_end="17:00", min_minutes=30):
    allbusy = [b for cal in calendars for b in cal]
    return free_slots(allbusy, day_start, day_end, min_minutes)


def first_slot(calendars, duration, day_start="09:00", day_end="17:00"):
    allbusy = [b for cal in calendars for b in cal]
    for a, b in _free(allbusy, _m(day_start), _m(day_end), duration):
        return (_f(a), _f(a + duration))
    return None
'''},
tests=r'''import unittest
from calendar_slots import free_slots, common_free, first_slot


class T(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(free_slots([("10:00", "11:00"), ("13:00", "14:30")]),
                         [("09:00", "10:00"), ("11:00", "13:00"), ("14:30", "17:00")])

    def test_empty(self): self.assertEqual(free_slots([]), [("09:00", "17:00")])

    def test_overlap_unsorted(self):
        self.assertEqual(free_slots([("13:00", "15:00"), ("9:30", "11:00"), ("10:30", "12:00")]),
                         [("09:00", "09:30"), ("12:00", "13:00"), ("15:00", "17:00")])

    def test_back_to_back(self):
        self.assertEqual(free_slots([("09:00", "10:00"), ("10:00", "12:00")]), [("12:00", "17:00")])

    def test_clip_outside_day(self):
        self.assertEqual(free_slots([("07:00", "09:45"), ("16:30", "19:00"), ("20:00", "21:00")]), [("09:45", "16:30")])

    def test_min_minutes(self):
        self.assertEqual(free_slots([("09:20", "12:00"), ("12:29", "16:00")], min_minutes=30), [("16:00", "17:00")])
        self.assertEqual(free_slots([("09:20", "12:00"), ("12:29", "16:00")], min_minutes=20),
                         [("09:00", "09:20"), ("12:00", "12:29"), ("16:00", "17:00")])

    def test_custom_day(self):
        self.assertEqual(free_slots([("23:00", "24:00")], day_start="0:00", day_end="24:00", min_minutes=60), [("00:00", "23:00")])

    def test_fully_busy(self): self.assertEqual(free_slots([("08:00", "18:00")]), [])

    def test_invalid(self):
        for b in [[("11:00", "10:00")], [("10:00", "10:00")], [("24:30", "25:00")], [("7:5", "8:00")], [("ab:cd", "10:00")], [("10:60", "11:00")]]:
            with self.subTest(b=b):
                with self.assertRaises(ValueError): free_slots(b)

    def test_common(self):
        a = [("09:00", "10:30"), ("12:00", "13:00")]
        b = [("10:00", "11:00"), ("15:00", "16:00")]
        self.assertEqual(common_free([a, b]), [("11:00", "12:00"), ("13:00", "15:00"), ("16:00", "17:00")])
        self.assertEqual(common_free([]), [("09:00", "17:00")])

    def test_first_slot(self):
        a = [("09:00", "10:30"), ("12:00", "13:00")]
        b = [("10:00", "11:00"), ("15:00", "16:00")]
        self.assertEqual(first_slot([a, b], 45), ("11:00", "11:45"))
        self.assertEqual(first_slot([a, b], 90), ("13:00", "14:30"))
        self.assertIsNone(first_slot([a, b], 150))
'''))

# ---------------------------------------------------------------- 12
TASKS.append(dict(
id="12_bank_concurrency_bugfix", difficulty="medium",
prompt=r'''`bank.py` is used by a multi-threaded payment service. Production incidents:
1. Under concurrent deposits money occasionally disappears or appears out of nowhere.
2. The service sometimes hangs forever while processing transfers.
3. Failed transfers sometimes leave partial changes.

Fix `bank.py` (keep the public API: `Account`, `transfer`, `Bank`, `InsufficientFunds`). Requirements:
- `Account.deposit`, `Account.withdraw` and `transfer(src, dst, amount)` must be thread-safe.
- `amount` must be > 0, else `ValueError`. Transferring to the same account raises `ValueError`.
- If `src` has insufficient funds raise `InsufficientFunds` and leave BOTH balances unchanged.
- Transfers running concurrently in opposite directions (A->B and B->A) must never deadlock.
- `Bank.open(owner, balance=0)` raises `ValueError` if `owner` already has an account.
''',
starter={"bank.py": r'''import threading
import time


class InsufficientFunds(Exception):
    pass


class Account:
    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance
        self.lock = threading.Lock()

    def deposit(self, amount):
        bal = self.balance
        time.sleep(0)
        self.balance = bal + amount

    def withdraw(self, amount):
        if self.balance < amount:
            raise InsufficientFunds(self.owner)
        bal = self.balance
        time.sleep(0)
        self.balance = bal - amount


def transfer(src, dst, amount):
    with src.lock:
        time.sleep(0)
        with dst.lock:
            src.withdraw(amount)
            dst.deposit(amount)


class Bank:
    def __init__(self):
        self.accounts = {}

    def open(self, owner, balance=0):
        acct = Account(owner, balance)
        self.accounts[owner] = acct
        return acct

    def total(self):
        return sum(a.balance for a in self.accounts.values())
'''},
ref={"bank.py": r'''import threading


class InsufficientFunds(Exception):
    pass


class Account:
    _seq = 0
    _seq_lock = threading.Lock()

    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance
        self.lock = threading.RLock()
        with Account._seq_lock:
            Account._seq += 1
            self._order = Account._seq

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("amount must be > 0")
        with self.lock:
            self.balance += amount

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("amount must be > 0")
        with self.lock:
            if self.balance < amount:
                raise InsufficientFunds(self.owner)
            self.balance -= amount


def transfer(src, dst, amount):
    if amount <= 0:
        raise ValueError("amount must be > 0")
    if src is dst:
        raise ValueError("cannot transfer to same account")
    first, second = (src, dst) if src._order < dst._order else (dst, src)
    with first.lock:
        with second.lock:
            if src.balance < amount:
                raise InsufficientFunds(src.owner)
            src.balance -= amount
            dst.balance += amount


class Bank:
    def __init__(self):
        self.accounts = {}
        self._lock = threading.Lock()

    def open(self, owner, balance=0):
        with self._lock:
            if owner in self.accounts:
                raise ValueError("account exists")
            acct = Account(owner, balance)
            self.accounts[owner] = acct
            return acct

    def total(self):
        return sum(a.balance for a in self.accounts.values())
'''},
tests=r'''import unittest, threading, random, sys
import bank
from bank import Account, transfer, Bank, InsufficientFunds

sys.setswitchinterval(1e-5)


def run_threads(fns, timeout=30):
    ts = [threading.Thread(target=f, daemon=True) for f in fns]
    for t in ts: t.start()
    for t in ts: t.join(timeout)
    return [t for t in ts if t.is_alive()]


class T(unittest.TestCase):
    def test_concurrent_deposits(self):
        a = Account('a', 0)
        def work():
            for _ in range(3000): a.deposit(1)
        self.assertEqual(run_threads([work] * 8), [])
        self.assertEqual(a.balance, 24000)

    def test_concurrent_withdrawals(self):
        a = Account('a', 10000); fails = []
        def work():
            for _ in range(2000):
                try: a.withdraw(1)
                except InsufficientFunds: fails.append(1)
        self.assertEqual(run_threads([work] * 8), [])
        self.assertEqual(a.balance, 0); self.assertEqual(len(fails), 6000)

    def test_no_deadlock_opposite(self):
        a, b = Account('a', 100000), Account('b', 100000)
        def ab():
            for _ in range(1500): transfer(a, b, 1)
        def ba():
            for _ in range(1500): transfer(b, a, 1)
        alive = run_threads([ab, ba] * 5, timeout=30)
        self.assertEqual(alive, [], "deadlock: threads still running")
        self.assertEqual(a.balance + b.balance, 200000); self.assertEqual(a.balance, 100000)

    def test_insufficient_unchanged(self):
        a, b = Account('a', 10), Account('b', 5)
        with self.assertRaises(InsufficientFunds): transfer(a, b, 20)
        self.assertEqual((a.balance, b.balance), (10, 5))

    def test_value_errors(self):
        a, b = Account('a', 10), Account('b', 5)
        for f in (lambda: a.deposit(0), lambda: a.withdraw(-1), lambda: transfer(a, b, 0), lambda: transfer(a, a, 1)):
            with self.assertRaises(ValueError): f()
        self.assertEqual((a.balance, b.balance), (10, 5))

    def test_random_conservation(self):
        bk = Bank(); accts = [bk.open('u%d' % i, 1000) for i in range(6)]
        def work(seed):
            rnd = random.Random(seed)
            def f():
                for _ in range(1500):
                    x, y = rnd.sample(accts, 2)
                    try: transfer(x, y, rnd.randint(1, 300))
                    except InsufficientFunds: pass
            return f
        self.assertEqual(run_threads([work(s) for s in range(8)]), [])
        self.assertEqual(bk.total(), 6000)
        self.assertTrue(all(a.balance >= 0 for a in accts))

    def test_duplicate_open(self):
        bk = Bank(); bk.open('x')
        with self.assertRaises(ValueError): bk.open('x')
'''))

# ---------------------------------------------------------------- 13
TASKS.append(dict(
id="13_autocomplete_trie", difficulty="easy",
prompt=r'''Create `autocomplete.py` with class `Autocomplete` (case-insensitive; all words are stored and returned lowercased):

- `add(word, weight=1)`: `word` must be a non-empty str and `weight` a positive int, else `ValueError`. Re-adding a word ADDS to its weight.
- `remove(word) -> bool`: remove the word; True if it existed.
- `weight(word) -> int`: current weight, 0 if absent.
- `suggest(prefix, k=5) -> list[str]`: up to `k` stored words starting with `prefix` (case-insensitive), sorted by weight
  descending, ties alphabetically ascending. Empty prefix considers all words. `k <= 0` returns `[]`.
- `__len__` (distinct words) and `__contains__`.
- Performance: with 100,000 words stored, thousands of `suggest()` calls with 3+ character prefixes must take well under a
  few seconds in total, so do not scan every word on each call (use a trie or similar index).
''',
starter={},
ref={"autocomplete.py": r'''class _Node:
    __slots__ = ("kids", "end")

    def __init__(self):
        self.kids = {}
        self.end = False


class Autocomplete:
    def __init__(self):
        self.root = _Node()
        self.w = {}

    def add(self, word, weight=1):
        if not isinstance(word, str) or not word:
            raise ValueError("word must be non-empty str")
        if not isinstance(weight, int) or isinstance(weight, bool) or weight <= 0:
            raise ValueError("weight must be positive int")
        word = word.lower()
        n = self.root
        for ch in word:
            n = n.kids.setdefault(ch, _Node())
        n.end = True
        self.w[word] = self.w.get(word, 0) + weight

    def remove(self, word):
        word = word.lower()
        if word not in self.w:
            return False
        del self.w[word]
        n = self.root
        for ch in word:
            n = n.kids[ch]
        n.end = False
        return True

    def weight(self, word):
        return self.w.get(word.lower(), 0)

    def suggest(self, prefix, k=5):
        if k <= 0:
            return []
        prefix = prefix.lower()
        n = self.root
        for ch in prefix:
            n = n.kids.get(ch)
            if n is None:
                return []
        found, stack = [], [(n, prefix)]
        while stack:
            node, s = stack.pop()
            if node.end:
                found.append(s)
            for ch, kid in node.kids.items():
                stack.append((kid, s + ch))
        found.sort(key=lambda x: (-self.w[x], x))
        return found[:k]

    def __len__(self):
        return len(self.w)

    def __contains__(self, word):
        return isinstance(word, str) and word.lower() in self.w
'''},
tests=r'''import unittest, random, time
from autocomplete import Autocomplete


class T(unittest.TestCase):
    def test_basic(self):
        a = Autocomplete()
        for w, x in [("apple", 5), ("app", 3), ("application", 5), ("apt", 1), ("banana", 9)]: a.add(w, x)
        self.assertEqual(a.suggest("ap"), ["apple", "application", "app", "apt"])
        self.assertEqual(a.suggest("ap", k=2), ["apple", "application"])
        self.assertEqual(a.suggest("b"), ["banana"]); self.assertEqual(a.suggest("z"), [])

    def test_case_insensitive(self):
        a = Autocomplete(); a.add("Hello", 2); a.add("help")
        self.assertEqual(a.suggest("HE"), ["hello", "help"]); self.assertIn("HELLO", a); self.assertEqual(a.weight("hElLo"), 2)

    def test_accumulate(self):
        a = Autocomplete(); a.add("x", 2); a.add("X", 3); self.assertEqual(a.weight("x"), 5); self.assertEqual(len(a), 1)

    def test_remove(self):
        a = Autocomplete(); a.add("car"); a.add("cart"); self.assertTrue(a.remove("car")); self.assertFalse(a.remove("car"))
        self.assertEqual(a.suggest("ca"), ["cart"]); self.assertNotIn("car", a); self.assertEqual(len(a), 1); self.assertEqual(a.weight("car"), 0)

    def test_empty_prefix_and_k(self):
        a = Autocomplete(); a.add("b", 1); a.add("a", 1); a.add("c", 2)
        self.assertEqual(a.suggest(""), ["c", "a", "b"]); self.assertEqual(a.suggest("", k=0), [])

    def test_validation(self):
        a = Autocomplete()
        for args in [("",), ("x", 0), ("x", -1), ("x", 1.5), (None,)]:
            with self.assertRaises(ValueError): a.add(*args)

    def test_performance(self):
        rnd = random.Random(2); a = Autocomplete(); words = set()
        while len(words) < 100000:
            words.add(''.join(rnd.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(rnd.randint(5, 10))))
        words = sorted(words)
        for w in words: a.add(w, rnd.randint(1, 100))
        qs = [w[:rnd.randint(3, 4)] for w in rnd.sample(words, 4000)]
        t = time.perf_counter()
        for q in qs: a.suggest(q, 5)
        self.assertLess(time.perf_counter() - t, 6.0)
        q = qs[0]; exp = sorted([w for w in words if w.startswith(q)], key=lambda w: (-a.weight(w), w))[:5]
        self.assertEqual(a.suggest(q, 5), exp)
'''))

# ---------------------------------------------------------------- 14
TASKS.append(dict(
id="14_cron_next_run", difficulty="hard",
prompt=r'''Create `cron.py` implementing standard 5-field cron schedules (minute hour day-of-month month day-of-week).

- `next_run(expr: str, after: datetime) -> datetime`: the first matching time STRICTLY after `after` (seconds/microseconds
  of the result are 0; `after` may have non-zero seconds). Naive datetimes.
- `upcoming(expr, after, n) -> list[datetime]`: the next `n` run times.

Field syntax (ranges: minute 0-59, hour 0-23, day-of-month 1-31, month 1-12, day-of-week 0-7 where 0 and 7 are Sunday):
- `*`, a number, a range `a-b` (a <= b), a step `*/s`, `a-b/s`, or `a/s` (= from a to the field maximum with step s; s >= 1),
  and comma-separated lists of these.
- Day matching: a field is "restricted" if it is not exactly `*`. If BOTH day-of-month and day-of-week are restricted, a day
  matches when EITHER matches; otherwise both must match (unrestricted fields match everything).
- Macros: `@hourly` = `0 * * * *`, `@daily` = `0 0 * * *`, `@weekly` = `0 0 * * 0`, `@monthly` = `0 0 1 * *`, `@yearly` = `0 0 1 1 *`.
- Invalid expressions (wrong field count, out-of-range values, a > b, step 0, junk) raise `ValueError`.
- If no matching time exists within 8 years after `after` (e.g. `0 0 30 2 *`), raise `ValueError`.
''',
starter={},
ref={"cron.py": r'''from datetime import datetime, timedelta, time as dtime

_RANGES = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 7)]
_MACROS = {"@hourly": "0 * * * *", "@daily": "0 0 * * *", "@weekly": "0 0 * * 0",
           "@monthly": "0 0 1 * *", "@yearly": "0 0 1 1 *"}


def _num(x):
    if not x.isdigit():
        raise ValueError("bad number %r" % x)
    return int(x)


def _field(spec, lo, hi):
    vals = set()
    for part in spec.split(','):
        if not part:
            raise ValueError("empty list item")
        step = 1
        if '/' in part:
            rng, st = part.split('/', 1)
            step = _num(st)
            if step <= 0:
                raise ValueError("step must be >= 1")
        else:
            rng = part
        if rng == '*':
            a, b = lo, hi
        elif '-' in rng:
            x, y = rng.split('-', 1)
            a, b = _num(x), _num(y)
            if a > b:
                raise ValueError("bad range")
        else:
            a = _num(rng)
            b = hi if '/' in part else a
        if a < lo or b > hi:
            raise ValueError("out of range")
        vals.update(range(a, b + 1, step))
    return vals


def _parse(expr):
    expr = _MACROS.get(expr.strip(), expr)
    parts = expr.split()
    if len(parts) != 5:
        raise ValueError("need 5 fields")
    fs = [_field(p, lo, hi) for p, (lo, hi) in zip(parts, _RANGES)]
    if 7 in fs[4]:
        fs[4].discard(7); fs[4].add(0)
    return fs, parts[2] != '*', parts[4] != '*'


def next_run(expr, after):
    (mins, hours, doms, months, dows), rdom, rdow = _parse(expr)
    mins, hours = sorted(mins), sorted(hours)
    t = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    day = t.date()
    limit = day + timedelta(days=366 * 8)
    while day <= limit:
        if day.month in months:
            dom_ok = day.day in doms
            dow_ok = (day.weekday() + 1) % 7 in dows
            ok = (dom_ok or dow_ok) if (rdom and rdow) else (dom_ok and dow_ok)
            if ok:
                for h in hours:
                    for m in mins:
                        cand = datetime(day.year, day.month, day.day, h, m)
                        if cand >= t:
                            return cand
        day += timedelta(days=1)
    raise ValueError("no matching time")


def upcoming(expr, after, n):
    out = []
    for _ in range(n):
        after = next_run(expr, after)
        out.append(after)
    return out
'''},
tests=r'''import unittest
from datetime import datetime as D
from cron import next_run, upcoming


class T(unittest.TestCase):
    def nr(self, e, a, exp): self.assertEqual(next_run(e, a), exp, e)

    def test_step(self):
        self.nr("*/15 * * * *", D(2026, 1, 1, 10, 7), D(2026, 1, 1, 10, 15))
        self.nr("*/15 * * * *", D(2026, 1, 1, 10, 15), D(2026, 1, 1, 10, 30))
        self.nr("*/15 * * * *", D(2026, 1, 1, 10, 14, 30), D(2026, 1, 1, 10, 15))
        self.nr("*/15 * * * *", D(2026, 1, 1, 23, 50), D(2026, 1, 2, 0, 0))

    def test_weekdays(self):
        self.nr("0 9 * * 1-5", D(2026, 10, 9, 17, 0), D(2026, 10, 12, 9, 0))
        self.nr("0 9 * * 1-5", D(2026, 10, 12, 8, 59, 59), D(2026, 10, 12, 9, 0))

    def test_leap(self): self.nr("30 2 29 2 *", D(2026, 3, 1), D(2028, 2, 29, 2, 30))
    def test_31st(self): self.nr("0 0 31 * *", D(2026, 4, 1), D(2026, 5, 31))

    def test_dom_dow_or(self):
        self.nr("0 12 13 * 5", D(2026, 10, 6), D(2026, 10, 9, 12, 0))
        self.nr("0 12 13 * 5", D(2026, 10, 9, 12, 0), D(2026, 10, 13, 12, 0))

    def test_dom_only(self): self.nr("0 12 13 * *", D(2026, 10, 6), D(2026, 10, 13, 12, 0))
    def test_dow_only_with_month(self): self.nr("0 0 * 12 1", D(2026, 10, 6), D(2026, 12, 7, 0, 0))
    def test_sunday_7(self): self.nr("0 0 * * 7", D(2026, 10, 6), D(2026, 10, 11)); self.nr("0 0 * * 0", D(2026, 10, 6), D(2026, 10, 11))

    def test_lists_ranges_steps(self):
        e = "5,10-12,50-59/4 * * * *"
        self.nr(e, D(2026, 1, 1, 10, 0), D(2026, 1, 1, 10, 5)); self.nr(e, D(2026, 1, 1, 10, 12), D(2026, 1, 1, 10, 50))
        self.nr(e, D(2026, 1, 1, 10, 54), D(2026, 1, 1, 10, 58)); self.nr(e, D(2026, 1, 1, 10, 58), D(2026, 1, 1, 11, 5))
        self.nr("1-30/10 * * * *", D(2026, 1, 1, 10, 21), D(2026, 1, 1, 11, 1))
        self.nr("7/20 * * * *", D(2026, 1, 1, 10, 30), D(2026, 1, 1, 10, 47))

    def test_year_rollover(self): self.nr("0 0 1 1 *", D(2026, 12, 31, 23, 59), D(2027, 1, 1))

    def test_macros(self):
        self.nr("@daily", D(2026, 10, 6, 0, 0), D(2026, 10, 7)); self.nr("@hourly", D(2026, 10, 6, 5, 59), D(2026, 10, 6, 6, 0))
        self.nr("@weekly", D(2026, 10, 6), D(2026, 10, 11)); self.nr("@monthly", D(2026, 10, 6), D(2026, 11, 1))
        self.nr("@yearly", D(2026, 10, 6), D(2027, 1, 1))

    def test_invalid(self):
        for e in ["60 * * * *", "* * * *", "* * * * * *", "*/0 * * * *", "5-1 * * * *", "a * * * *", "* * 0 * *",
                  "* * * 13 *", "* 24 * * *", "* * * * 8", "1,,2 * * * *", "", "@never"]:
            with self.subTest(e=e):
                with self.assertRaises(ValueError): next_run(e, D(2026, 1, 1))

    def test_impossible(self):
        with self.assertRaises(ValueError): next_run("0 0 30 2 *", D(2026, 1, 1))

    def test_upcoming(self):
        self.assertEqual(upcoming("0 */6 * * *", D(2026, 10, 6, 5, 0), 4),
                         [D(2026, 10, 6, 6), D(2026, 10, 6, 12), D(2026, 10, 6, 18), D(2026, 10, 7, 0)])
'''))

# ---------------------------------------------------------------- 15
TASKS.append(dict(
id="15_markdown_renderer", difficulty="hard",
prompt=r'''Create `md.py` with `render(text: str) -> str`, converting a Markdown subset to HTML. Output blocks are joined with
`"\n"` (no trailing newline); an empty/blank document renders to `""`.

Block rules (process line by line; markers are at column 0):
1. Fenced code: a line starting with three backticks opens a block (optional language word after them); it closes at the next
   line that is exactly three backticks (ignoring trailing whitespace) or at end of document. Content lines are HTML-escaped and
   joined with `\n`: `<pre><code>CONTENT</code></pre>`, or `<pre><code class="language-LANG">CONTENT</code></pre>` if a language is given.
   No inline formatting inside code blocks.
2. Heading: 1-6 `#` followed by a space: `<hN>INLINE</hN>` (text stripped). `#######` or `#x` are not headings.
3. Unordered list: consecutive lines starting with `- ` or `* ` -> `<ul><li>INLINE</li>...</ul>` on one line.
4. Ordered list: consecutive lines matching `<digits>. ` -> `<ol><li>INLINE</li>...</ol>` on one line. Switching between `ul`
   and `ol` lines starts a new list.
5. Blank lines separate blocks.
6. Paragraph: consecutive other non-blank lines, each stripped, joined by a single space: `<p>INLINE</p>`. A heading, list item
   or fence line ends the paragraph (and starts its own block).

Inline rules (headings, list items, paragraphs):
- HTML-escape `&`, `<`, `>` in text.
- Code spans `` `code` `` -> `<code>code</code>` (content escaped, no further formatting inside).
- Links `[text](url)` -> `<a href="url">text</a>` (text gets bold/italic formatting; in the url escape `&` as `&amp;` and `"` as `&quot;`).
- `**x**` -> `<strong>x</strong>`, then `*x*` -> `<em>x</em>`, where x is non-empty and does not start or end with whitespace.
- Unmatched markers stay literal.
''',
starter={},
ref={"md.py": r'''import re

_LINK = re.compile(r'\[([^\]]+)\]\(([^)\s]+)\)')
_BOLD = re.compile(r'\*\*(?!\s)(.+?)(?<!\s)\*\*')
_EM = re.compile(r'\*(?!\s)(.+?)(?<!\s)\*')
_OL = re.compile(r'^\d+\. ')
_H = re.compile(r'^(#{1,6}) (.*)$')


def _esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _emph(t):
    t = _BOLD.sub(r'<strong>\1</strong>', t)
    return _EM.sub(r'<em>\1</em>', t)


def _fmt(s):
    out, pos = [], 0
    for m in _LINK.finditer(s):
        out.append(_emph(_esc(s[pos:m.start()])))
        url = m.group(2).replace('&', '&amp;').replace('"', '&quot;')
        out.append('<a href="%s">%s</a>' % (url, _emph(_esc(m.group(1)))))
        pos = m.end()
    out.append(_emph(_esc(s[pos:])))
    return ''.join(out)


def _inline(s):
    out = []
    for p in re.split(r'(`[^`]*`)', s):
        if len(p) >= 2 and p[0] == '`' and p[-1] == '`':
            out.append('<code>' + _esc(p[1:-1]) + '</code>')
        else:
            out.append(_fmt(p))
    return ''.join(out)


def _kind(line):
    if line.startswith('```'): return 'fence'
    if _H.match(line): return 'h'
    if line.startswith('- ') or line.startswith('* '): return 'ul'
    if _OL.match(line): return 'ol'
    if not line.strip(): return 'blank'
    return 'p'


def render(text):
    lines = text.split('\n')
    blocks, i = [], 0
    while i < len(lines):
        line = lines[i]; k = _kind(line)
        if k == 'blank':
            i += 1
        elif k == 'fence':
            lang = line[3:].strip(); i += 1; body = []
            while i < len(lines) and lines[i].rstrip() != '```':
                body.append(_esc(lines[i])); i += 1
            i += 1
            cls = ' class="language-%s"' % lang if lang else ''
            blocks.append('<pre><code%s>%s</code></pre>' % (cls, '\n'.join(body)))
        elif k == 'h':
            m = _H.match(line); n = len(m.group(1))
            blocks.append('<h%d>%s</h%d>' % (n, _inline(m.group(2).strip()), n)); i += 1
        elif k in ('ul', 'ol'):
            items = []
            while i < len(lines) and _kind(lines[i]) == k:
                body = lines[i][2:] if k == 'ul' else _OL.sub('', lines[i], count=1)
                items.append('<li>%s</li>' % _inline(body.strip())); i += 1
            blocks.append('<%s>%s</%s>' % (k, ''.join(items), k))
        else:
            para = []
            while i < len(lines) and _kind(lines[i]) == 'p':
                para.append(lines[i].strip()); i += 1
            blocks.append('<p>%s</p>' % _inline(' '.join(para)))
    return '\n'.join(blocks)
'''},
tests=r'''import unittest
from md import render


class T(unittest.TestCase):
    def r(self, src, exp): self.assertEqual(render(src), exp, repr(src))

    def test_headings(self):
        self.r("# Title", "<h1>Title</h1>"); self.r("###### six", "<h6>six</h6>")
        self.r("####### seven", "<p>####### seven</p>"); self.r("#nospace", "<p>#nospace</p>")
        self.r("## Hello *world*", "<h2>Hello <em>world</em></h2>")

    def test_paragraphs(self):
        self.r("line one\nline two\n\npara two", "<p>line one line two</p>\n<p>para two</p>")
        self.r("  hi  \n  there", "<p>hi there</p>")

    def test_inline(self):
        self.r("This is **bold** and *it* and `co*de*`", "<p>This is <strong>bold</strong> and <em>it</em> and <code>co*de*</code></p>")
        self.r("**a *b* c**", "<p><strong>a <em>b</em> c</strong></p>")

    def test_link(self):
        self.r("See [the **docs**](http://x.com/?a=1&b=2).", '<p>See <a href="http://x.com/?a=1&amp;b=2">the <strong>docs</strong></a>.</p>')

    def test_escape(self):
        self.r("a < b & c > d", "<p>a &lt; b &amp; c &gt; d</p>"); self.r("`<x>`", "<p><code>&lt;x&gt;</code></p>")

    def test_lists(self):
        self.r("- one\n- two\n* three", "<ul><li>one</li><li>two</li><li>three</li></ul>")
        self.r("1. a\n2. b\n10. c", "<ol><li>a</li><li>b</li><li>c</li></ol>")
        self.r("- a\n1. b", "<ul><li>a</li></ul>\n<ol><li>b</li></ol>")
        self.r("- **x**", "<ul><li><strong>x</strong></li></ul>")

    def test_interrupt(self): self.r("para\n- item\n# H", "<p>para</p>\n<ul><li>item</li></ul>\n<h1>H</h1>")

    def test_fence(self):
        self.r("```python\nx = 1 < 2\n**no**\n```\nafter", '<pre><code class="language-python">x = 1 &lt; 2\n**no**</code></pre>\n<p>after</p>')
        self.r("```\na\nb", "<pre><code>a\nb</code></pre>")
        self.r("```\na\n\nb\n```", "<pre><code>a\n\nb</code></pre>")
        self.r("text\n```\ncode\n```", "<p>text</p>\n<pre><code>code</code></pre>")

    def test_blank(self):
        self.r("\n\n# A\n\n\n", "<h1>A</h1>"); self.r("", ""); self.r("   \n  ", "")

    def test_unmatched(self):
        self.r("a ** b", "<p>a ** b</p>"); self.r("*a", "<p>*a</p>"); self.r("[x](", "<p>[x](</p>")
'''))
