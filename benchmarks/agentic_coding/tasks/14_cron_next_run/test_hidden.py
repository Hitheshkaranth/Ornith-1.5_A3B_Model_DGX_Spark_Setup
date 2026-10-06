import unittest
from datetime import datetime as D
from cron import next_run, upcoming


class T(unittest.TestCase):
    def nr(self, e, a, exp): self.assertEqual(next_run(e, a), exp, e)

    def test_step(self):
        self.nr("*/15 * * * *", D(2026, 1, 1, 10, 7), D(2026, 1, 1, 10, 15))
        self.nr("*/15 * * * *", D(2026, 1, 1, 10, 15), D(2026, 1, 1, 10, 30))
        self.nr("*/15 * * * *", D(2026, 1, 1, 10, 14, 30), D(2026, 1, 1, 10, 15))
        self.nr("*/15 * * * *", D(2026, 1, 1, 23, 50), D(2026, 1, 2, 0, 0))

    def test_weekdays(self):
        self.nr("0 9 * * 1-5", D(2026, 10, 9, 17, 0), D(2026, 10, 12, 9, 0))
        self.nr("0 9 * * 1-5", D(2026, 10, 12, 8, 59, 59), D(2026, 10, 12, 9, 0))

    def test_leap(self): self.nr("30 2 29 2 *", D(2026, 3, 1), D(2028, 2, 29, 2, 30))
    def test_31st(self): self.nr("0 0 31 * *", D(2026, 4, 1), D(2026, 5, 31))

    def test_dom_dow_or(self):
        self.nr("0 12 13 * 5", D(2026, 10, 6), D(2026, 10, 9, 12, 0))
        self.nr("0 12 13 * 5", D(2026, 10, 9, 12, 0), D(2026, 10, 13, 12, 0))

    def test_dom_only(self): self.nr("0 12 13 * *", D(2026, 10, 6), D(2026, 10, 13, 12, 0))
    def test_dow_only_with_month(self): self.nr("0 0 * 12 1", D(2026, 10, 6), D(2026, 12, 7, 0, 0))
    def test_sunday_7(self): self.nr("0 0 * * 7", D(2026, 10, 6), D(2026, 10, 11)); self.nr("0 0 * * 0", D(2026, 10, 6), D(2026, 10, 11))

    def test_lists_ranges_steps(self):
        e = "5,10-12,50-59/4 * * * *"
        self.nr(e, D(2026, 1, 1, 10, 0), D(2026, 1, 1, 10, 5)); self.nr(e, D(2026, 1, 1, 10, 12), D(2026, 1, 1, 10, 50))
        self.nr(e, D(2026, 1, 1, 10, 54), D(2026, 1, 1, 10, 58)); self.nr(e, D(2026, 1, 1, 10, 58), D(2026, 1, 1, 11, 5))
        self.nr("1-30/10 * * * *", D(2026, 1, 1, 10, 21), D(2026, 1, 1, 11, 1))
        self.nr("7/20 * * * *", D(2026, 1, 1, 10, 30), D(2026, 1, 1, 10, 47))

    def test_year_rollover(self): self.nr("0 0 1 1 *", D(2026, 12, 31, 23, 59), D(2027, 1, 1))

    def test_macros(self):
        self.nr("@daily", D(2026, 10, 6, 0, 0), D(2026, 10, 7)); self.nr("@hourly", D(2026, 10, 6, 5, 59), D(2026, 10, 6, 6, 0))
        self.nr("@weekly", D(2026, 10, 6), D(2026, 10, 11)); self.nr("@monthly", D(2026, 10, 6), D(2026, 11, 1))
        self.nr("@yearly", D(2026, 10, 6), D(2027, 1, 1))

    def test_invalid(self):
        for e in ["60 * * * *", "* * * *", "* * * * * *", "*/0 * * * *", "5-1 * * * *", "a * * * *", "* * 0 * *",
                  "* * * 13 *", "* 24 * * *", "* * * * 8", "1,,2 * * * *", "", "@never"]:
            with self.subTest(e=e):
                with self.assertRaises(ValueError): next_run(e, D(2026, 1, 1))

    def test_impossible(self):
        with self.assertRaises(ValueError): next_run("0 0 30 2 *", D(2026, 1, 1))

    def test_upcoming(self):
        self.assertEqual(upcoming("0 */6 * * *", D(2026, 10, 6, 5, 0), 4),
                         [D(2026, 10, 6, 6), D(2026, 10, 6, 12), D(2026, 10, 6, 18), D(2026, 10, 7, 0)])
