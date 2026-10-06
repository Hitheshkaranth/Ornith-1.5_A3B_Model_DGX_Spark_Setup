"""Find free meeting slots given a list of busy intervals."""

_END_OF_DAY = 24 * 60  # 1440 minutes, i.e. "24:00"


def _parse_time(value):
    """Parse "H:MM" or "HH:MM" into minutes since midnight (0..1440).

    Raises ValueError for anything outside the accepted format or range.
    """
    if not isinstance(value, str):
        raise ValueError("Time must be a string, got {!r}".format(value))

    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError("Time must have the form 'H:MM' or 'HH:MM': {!r}".format(value))

    h_str, m_str = parts
    if not (1 <= len(h_str) <= 2):
        raise ValueError("Hours must be 1-2 digits: {!r}".format(value))
    if len(m_str) != 2:
        raise ValueError("Minutes must be exactly 2 digits: {!r}".format(value))
    if not all(c in "0123456789" for c in h_str):
        raise ValueError("Hours must be numeric: {!r}".format(value))
    if not all(c in "0123456789" for c in m_str):
        raise ValueError("Minutes must be numeric: {!r}".format(value))

    h = int(h_str)
    m = int(m_str)
    if not (0 <= h <= 24):
        raise ValueError("Hours must be 0-24: {!r}".format(value))
    if not (0 <= m <= 59):
        raise ValueError("Minutes must be 0-59: {!r}".format(value))
    if h == 24 and m != 0:
        raise ValueError("'24:00' is the only valid 24-hour time: {!r}".format(value))

    return h * 60 + m


def _format_time(minutes):
    """Format minutes since midnight as a zero-padded "HH:MM" string."""
    if not (0 <= minutes <= _END_OF_DAY):
        raise ValueError("Minutes out of range: {}".format(minutes))
    h, m = divmod(minutes, 60)
    return "{:02d}:{:02d}".format(h, m)


def _free_intervals(busy, ds, de):
    """Return sorted disjoint free minute-intervals within [ds, de]."""
    busy_intervals = []
    for b in busy:
        bs = _parse_time(b[0])
        be = _parse_time(b[1])
        if not (bs < be):
            raise ValueError("Busy block must satisfy start < end: {!r}".format(b))
        cs = max(bs, ds)
        ce = min(be, de)
        if cs < ce:
            busy_intervals.append((cs, ce))

    busy_intervals.sort()

    free = []
    cursor = ds
    for cs, ce in busy_intervals:
        if cs > cursor:
            free.append((cursor, cs))
        if ce > cursor:
            cursor = ce
    if de > cursor:
        free.append((cursor, de))
    return free


def free_slots(busy, day_start="09:00", day_end="17:00", min_minutes=30):
    """Return sorted free intervals inside [day_start, day_end] lasting >= min_minutes.

    Busy blocks may overlap, be unsorted, or extend outside the day (clipped).
    """
    ds = _parse_time(day_start)
    de = _parse_time(day_end)

    result = []
    for s, e in _free_intervals(busy, ds, de):
        if e - s >= min_minutes:
            result.append((_format_time(s), _format_time(e)))
    return result


def common_free(calendars, day_start="09:00", day_end="17:00", min_minutes=30):
    """Return intervals when EVERY person (calendar) is free."""
    ds = _parse_time(day_start)
    de = _parse_time(day_end)

    if calendars:
        free = _free_intervals(calendars[0], ds, de)
        for person in calendars[1:]:
            free = _intersect(free, _free_intervals(person, ds, de))
    else:
        free = [(ds, de)]

    return [
        (_format_time(s), _format_time(e))
        for s, e in free
        if e - s >= min_minutes
    ]


def _intersect(a, b):
    """Intersect two sorted lists of disjoint intervals."""
    result = []
    i = j = 0
    while i < len(a) and j < len(b):
        lo = max(a[i][0], b[j][0])
        hi = min(a[i][1], b[j][1])
        if lo < hi:
            result.append((lo, hi))
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return result


def first_slot(calendars, duration, day_start="09:00", day_end="17:00"):
    """Return the earliest (start, end) of exactly `duration` minutes where everyone
    is free, or None if no such slot exists."""
    ds = _parse_time(day_start)
    de = _parse_time(day_end)

    if calendars:
        free = _free_intervals(calendars[0], ds, de)
        for person in calendars[1:]:
            free = _intersect(free, _free_intervals(person, ds, de))
    else:
        free = [(ds, de)]

    for s, e in free:
        if e - s >= duration:
            return (_format_time(s), _format_time(s + duration))
    return None
