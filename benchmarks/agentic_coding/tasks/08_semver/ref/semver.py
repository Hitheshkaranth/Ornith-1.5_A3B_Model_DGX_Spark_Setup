import re

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
