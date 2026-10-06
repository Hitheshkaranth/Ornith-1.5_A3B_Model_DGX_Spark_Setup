from datetime import date, timedelta


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
