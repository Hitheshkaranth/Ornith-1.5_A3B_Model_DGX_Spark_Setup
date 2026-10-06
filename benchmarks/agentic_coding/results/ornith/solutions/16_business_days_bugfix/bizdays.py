from datetime import date, timedelta


def is_business_day(d, holidays=()):
    return d.weekday() < 5 and d not in holidays


def add_business_days(start, n, holidays=()):
    if n == 0:
        return start if is_business_day(start, holidays) else next_business_day(start, holidays)
    step = 1 if n > 0 else -1
    remaining = abs(n)
    d = start
    while remaining > 0:
        d += timedelta(days=step)
        if is_business_day(d, holidays):
            remaining -= 1
    return d


def business_days_between(a, b, holidays=()):
    if b < a:
        return -business_days_between(b, a, holidays)
    count = 0
    d = a
    while d < b:
        if is_business_day(d, holidays):
            count += 1
        d += timedelta(days=1)
    return count


def next_business_day(d, holidays=()):
    return add_business_days(d, 1, holidays)