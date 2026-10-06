"""Standard 5-field cron schedule parsing and next-run computation."""

from datetime import datetime, timedelta

MACROS = {
    '@hourly': '0 * * * *',
    '@daily': '0 0 * * *',
    '@weekly': '0 0 * * 0',
    '@monthly': '0 0 1 * *',
    '@yearly': '0 0 1 1 *',
    '@annually': '0 0 1 1 *',
    '@midnight': '0 0 * * *',
}

EIGHT_YEARS = 8


def _parse_field(field, lo, hi):
    """Parse a single cron field into the set of accepted integer values."""
    if not isinstance(field, str):
        raise ValueError('field must be a string')
    values = set()
    for part in field.split(','):
        if part == '':
            raise ValueError('empty element in field %r' % field)
        base = part
        step = 1
        if '/' in part:
            base, _, step_str = part.partition('/')
            if not step_str.isdigit() or int(step_str) == 0:
                raise ValueError('invalid step in field %r' % field)
            step = int(step_str)
        if base == '*':
            start, end = lo, hi
        elif '-' in base:
            a_str, _, b_str = base.partition('-')
            a = int(a_str)
            b = int(b_str)
            if a > b:
                raise ValueError('range start greater than end in %r' % field)
            start, end = a, b
        else:
            a = int(base)
            if step == 1:
                start, end = a, a
            else:
                start, end = a, hi
        if start < lo or end > hi:
            raise ValueError('value out of range in field %r' % field)
        for v in range(start, end + 1, step):
            values.add(v)
    if not values:
        raise ValueError('no values parsed from field %r' % field)
    return values


def _day_matches(dt, dom_values, dow_values, dom_restricted, dow_restricted):
    dom_match = dt.day in dom_values
    cron_dow = (dt.weekday() + 1) % 7
    dow_match = cron_dow in dow_values
    if dom_restricted and dow_restricted:
        return dom_match or dow_match
    return dom_match and dow_match


def _next_minute(dt, minutes_s):
    for m in minutes_s:
        if m >= dt.minute:
            return dt.replace(minute=m, second=0, microsecond=0)
    return (dt + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)


def _next_hour(dt, hours_s):
    for h in hours_s:
        if h >= dt.hour:
            return dt.replace(hour=h, minute=0, second=0, microsecond=0)
    return _next_day(dt)


def _next_day(dt):
    return (dt + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)


def _next_month(dt):
    if dt.month == 12:
        dt = dt.replace(year=dt.year + 1, month=1)
    else:
        dt = dt.replace(month=dt.month + 1)
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _add_years(dt, years):
    try:
        return dt.replace(year=dt.year + years)
    except ValueError:
        return dt.replace(year=dt.year + years, month=2, day=28)


def next_run(expr, after):
    if not isinstance(expr, str):
        raise ValueError('expression must be a string')

    text = expr.strip()
    if text.startswith('@'):
        if text not in MACROS:
            raise ValueError('unknown macro %r' % expr)
        text = MACROS[text]

    parts = text.split()
    if len(parts) != 5:
        raise ValueError('expected 5 fields, got %d' % len(parts))
    minute_field, hour_field, dom_field, month_field, dow_field = parts

    minutes = _parse_field(minute_field, 0, 59)
    hours = _parse_field(hour_field, 0, 23)
    dom_values = _parse_field(dom_field, 1, 31)
    month_values = _parse_field(month_field, 1, 12)
    dow_values = _parse_field(dow_field, 0, 7)
    dow_values = {v % 7 for v in dow_values}
    dom_restricted = dom_field != '*'
    dow_restricted = dow_field != '*'

    minutes_s = sorted(minutes)
    hours_s = sorted(hours)

    start = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    deadline = _add_years(after, EIGHT_YEARS)

    dt = start
    while dt < deadline:
        if dt.month not in month_values:
            dt = _next_month(dt)
            continue
        if not _day_matches(dt, dom_values, dow_values, dom_restricted, dow_restricted):
            dt = _next_day(dt)
            continue
        if dt.hour not in hours:
            dt = _next_hour(dt, hours_s)
            continue
        if dt.minute not in minutes:
            dt = _next_minute(dt, minutes_s)
            continue
        return dt
    raise ValueError('no matching time within 8 years')


def upcoming(expr, after, n):
    result = []
    cur = after
    for _ in range(n):
        cur = next_run(expr, cur)
        result.append(cur)
    return result