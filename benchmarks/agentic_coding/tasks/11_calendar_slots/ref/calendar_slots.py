import re

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
