from datetime import date

import bizdays


def test_is_business_day():
    assert bizdays.is_business_day(date(2024, 1, 6)) is False   # Saturday
    assert bizdays.is_business_day(date(2024, 1, 7)) is False   # Sunday
    assert bizdays.is_business_day(date(2024, 1, 8)) is True    # Monday
    assert bizdays.is_business_day(date(2024, 12, 24)) is True  # Tuesday
    # Dec 25 2024 is a Wednesday; it's a business day unless listed as a holiday
    assert bizdays.is_business_day(date(2024, 12, 25)) is True
    assert bizdays.is_business_day(date(2024, 12, 25), [date(2024, 12, 25)]) is False
    assert bizdays.is_business_day(date(2024, 12, 26)) is True


def test_is_business_day_holidays_container_types():
    one = date(2024, 12, 25)
    assert bizdays.is_business_day(one, [one]) is False
    assert bizdays.is_business_day(one, {one}) is False
    assert bizdays.is_business_day(one, (one,)) is False


def test_next_business_day():
    assert bizdays.next_business_day(date(2024, 1, 6)) == date(2024, 1, 8)  # Sat -> Mon
    assert bizdays.next_business_day(date(2024, 1, 5)) == date(2024, 1, 8)  # Fri -> next Mon
    one = date(2024, 12, 25)
    assert bizdays.next_business_day(one) == date(2024, 12, 26)


def test_add_business_days_forward():
    assert bizdays.add_business_days(date(2024, 1, 5), 1) == date(2024, 1, 8)  # Fri +1 -> Mon
    assert bizdays.add_business_days(date(2024, 1, 8), 1) == date(2024, 1, 9)


def test_add_business_days_zero():
    assert bizdays.add_business_days(date(2024, 1, 8), 0) == date(2024, 1, 8)   # business day
    assert bizdays.add_business_days(date(2024, 1, 6), 0) == date(2024, 1, 8)   # Saturday -> next


def test_add_business_days_negative():
    assert bizdays.add_business_days(date(2024, 1, 8), -1) == date(2024, 1, 5)  # Mon -1 -> Fri
    assert bizdays.add_business_days(date(2024, 1, 9), -1) == date(2024, 1, 8)


def test_add_business_days_skips_holidays():
    one = date(2024, 12, 25)  # Wednesday
    assert bizdays.add_business_days(one, 1) == date(2024, 12, 26)
    assert bizdays.add_business_days(date(2024, 12, 24), 1, [one]) == date(2024, 12, 26)
    assert bizdays.add_business_days(date(2024, 12, 27), -1, [one]) == date(2024, 12, 26)


def test_business_days_between_exclusive_end():
    assert bizdays.business_days_between(date(2024, 1, 1), date(2024, 1, 8)) == 5  # Mon-Fri
    assert bizdays.business_days_between(date(2024, 1, 5), date(2024, 1, 8)) == 1  # Fri only (end excluded)
    # end exclusive: Fri to next Fri is 5
    assert bizdays.business_days_between(date(2024, 1, 5), date(2024, 1, 12)) == 5


def test_business_days_between_negative_and_holidays():
    a = date(2024, 1, 1)
    b = date(2024, 1, 8)
    assert bizdays.business_days_between(b, a) == -bizdays.business_days_between(a, b)
    one = date(2024, 12, 25)
    assert bizdays.business_days_between(one, date(2024, 12, 27), [one]) == 1


if __name__ == "__main__":
    for _, fn in sorted(globals().items()):
        if callable(fn) and fn.__name__.startswith("test_"):
            fn()
    print("ALL TESTS PASSED")