import unittest
from datetime import date
from bizdays import is_business_day, add_business_days, business_days_between, next_business_day

TUE, FRI, SAT, SUN, MON = date(2026, 10, 6), date(2026, 10, 9), date(2026, 10, 10), date(2026, 10, 11), date(2026, 10, 12)


class T(unittest.TestCase):
    def test_is_business(self):
        self.assertTrue(is_business_day(TUE)); self.assertFalse(is_business_day(SAT)); self.assertFalse(is_business_day(SUN))
        self.assertFalse(is_business_day(TUE, [TUE]))

    def test_add_forward(self):
        self.assertEqual(add_business_days(TUE, 3), FRI); self.assertEqual(add_business_days(TUE, 4), MON)
        self.assertEqual(add_business_days(FRI, 1), MON); self.assertEqual(add_business_days(SAT, 1), MON)

    def test_add_zero(self):
        self.assertEqual(add_business_days(TUE, 0), TUE); self.assertEqual(add_business_days(SAT, 0), MON)
        self.assertEqual(add_business_days(FRI, 0, {FRI}), MON)

    def test_add_backward(self):
        self.assertEqual(add_business_days(MON, -1), FRI); self.assertEqual(add_business_days(SUN, -1), FRI)
        self.assertEqual(add_business_days(MON, -5), date(2026, 10, 5))

    def test_holidays(self):
        self.assertEqual(add_business_days(FRI, 1, {MON}), date(2026, 10, 13))
        self.assertEqual(add_business_days(date(2026, 10, 13), -1, [MON]), FRI)
        self.assertEqual(add_business_days(FRI, 1, (MON,)), date(2026, 10, 13))

    def test_between(self):
        self.assertEqual(business_days_between(MON, date(2026, 10, 19)), 5)
        self.assertEqual(business_days_between(TUE, TUE), 0); self.assertEqual(business_days_between(TUE, date(2026, 10, 7)), 1)
        self.assertEqual(business_days_between(date(2026, 10, 19), MON), -5)
        self.assertEqual(business_days_between(MON, date(2026, 10, 19), [date(2026, 10, 14)]), 4)
        self.assertEqual(business_days_between(SAT, MON), 0)

    def test_next(self):
        self.assertEqual(next_business_day(FRI), MON); self.assertEqual(next_business_day(FRI, [MON]), date(2026, 10, 13))
        self.assertEqual(next_business_day(TUE), date(2026, 10, 7))

    def test_consistency(self):
        hol = [date(2026, 12, 25), date(2027, 1, 1)]
        for n in range(-40, 41):
            d = add_business_days(TUE, n, hol)
            self.assertTrue(is_business_day(d, hol))
            self.assertEqual(business_days_between(TUE, d, hol), n)
