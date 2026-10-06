from datetime import datetime, timedelta, time as dtime

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
