from datetime import date, timedelta


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
