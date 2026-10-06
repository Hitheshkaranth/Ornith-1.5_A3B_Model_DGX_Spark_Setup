import unittest
from datetime import datetime, timedelta

from cron import next_run, upcoming


class TestBasics(unittest.TestCase):
    def test_every_minute_strictly_after(self):
        self.assertEqual(next_run('* * * * *', datetime(2023, 1, 1, 0, 0)),
                         datetime(2023, 1, 1, 0, 1))

    def test_every_minute_after_with_seconds(self):
        self.assertEqual(next_run('* * * * *', datetime(2023, 1, 1, 0, 0, 30)),
                         datetime(2023, 1, 1, 0, 1))

    def test_specific_minute(self):
        self.assertEqual(next_run('30 14 * * *', datetime(2023, 1, 1, 0, 0)),
                         datetime(2023, 1, 1, 14, 30))

    def test_specific_minute_next_day(self):
        self.assertEqual(next_run('30 14 * * *', datetime(2023, 1, 1, 15, 0)),
                         datetime(2023, 1, 2, 14, 30))

    def test_seconds_zero(self):
        r = next_run('5 6 * * *', datetime(2023, 1, 1, 0, 0))
        self.assertEqual((r.second, r.microsecond), (0, 0))


class TestStepsAndRanges(unittest.TestCase):
    def test_step_all(self):
        self.assertEqual(next_run('*/15 * * * *', datetime(2023, 1, 1, 0, 0)),
                         datetime(2023, 1, 1, 0, 15))

    def test_step_from_value(self):
        self.assertEqual(next_run('5/15 * * * *', datetime(2023, 1, 1, 0, 0)),
                         datetime(2023, 1, 1, 0, 5))

    def test_list(self):
        self.assertEqual(next_run('0,30 9 * * *', datetime(2023, 1, 1, 0, 0)),
                         datetime(2023, 1, 1, 9, 0))

    def test_range_hour_minute(self):
        self.assertEqual(next_run('*/10 9-17 * * *', datetime(2023, 1, 1, 8, 0)),
                         datetime(2023, 1, 1, 9, 0))

    def test_step_crosses_hour_boundary(self):
        # minutes {10,30,50}; hour range 9-17; after 09:55 the hour has no
        # later matching minute, so it rolls to the next hour's 10.
        self.assertEqual(next_run('10,30,50 9-17 * * *', datetime(2023, 1, 1, 9, 55)),
                         datetime(2023, 1, 1, 10, 10))


class TestDayOfWeek(unittest.TestCase):
    def test_weekly_sunday(self):
        # 2023-01-01 is a Sunday.
        self.assertEqual(next_run('0 0 * * 0', datetime(2023, 1, 1, 0, 0)),
                         datetime(2023, 1, 8, 0, 0))

    def test_dow_sunday_equivalent_0_and_7(self):
        r0 = next_run('0 0 * * 0', datetime(2023, 1, 1, 12, 0))
        r7 = next_run('0 0 * * 7', datetime(2023, 1, 1, 12, 0))
        self.assertEqual(r0, r7)

    def test_dow_friday(self):
        self.assertEqual(next_run('0 0 * * 5', datetime(2023, 1, 1, 0, 0)),
                         datetime(2023, 1, 6, 0, 0))


class TestDomDowLogic(unittest.TestCase):
    def test_both_restricted_either_match(self):
        # dom=13 OR dow=Friday. Fridays in Jan 2023: 6,13,20,27.
        # First match after Jan 1 00:00 is Jan 6 (a Friday), before the 13th.
        self.assertEqual(next_run('0 0 13 * 5', datetime(2023, 1, 1, 0, 0)),
                         datetime(2023, 1, 6, 0, 0))

    def test_dom_only(self):
        self.assertEqual(next_run('0 0 15 * *', datetime(2023, 1, 1, 0, 0)),
                         datetime(2023, 1, 15, 0, 0))

    def test_unrestricted_dom_only_matches_every_day(self):
        self.assertEqual(next_run('0 0 1 * *', datetime(2023, 1, 15, 0, 0)),
                         datetime(2023, 2, 1, 0, 0))

    def test_dom_31_skips_feb(self):
        self.assertEqual(next_run('0 0 31 * *', datetime(2023, 1, 31, 12, 0)),
                         datetime(2023, 3, 31, 0, 0))

    def test_dow_only_every_friday(self):
        self.assertEqual(next_run('0 0 * * 5', datetime(2023, 1, 6, 12, 0)),
                         datetime(2023, 1, 13, 0, 0))


class TestMacros(unittest.TestCase):
    def test_hourly(self):
        self.assertEqual(next_run('@hourly', datetime(2023, 1, 1, 5, 30)),
                         datetime(2023, 1, 1, 6, 0))

    def test_daily(self):
        self.assertEqual(next_run('@daily', datetime(2023, 1, 1, 12, 0)),
                         datetime(2023, 1, 2, 0, 0))

    def test_weekly(self):
        self.assertEqual(next_run('@weekly', datetime(2023, 1, 1, 12, 0)),
                         datetime(2023, 1, 8, 0, 0))

    def test_monthly(self):
        self.assertEqual(next_run('@monthly', datetime(2023, 1, 15, 0, 0)),
                         datetime(2023, 2, 1, 0, 0))

    def test_yearly(self):
        self.assertEqual(next_run('@yearly', datetime(2023, 6, 15, 0, 0)),
                         datetime(2024, 1, 1, 0, 0))

    def test_yearly_near_dec31(self):
        # after 2023-12-31 23:59 -> 2024-01-01 00:00
        self.assertEqual(next_run('@yearly', datetime(2023, 12, 31, 23, 59)),
                         datetime(2024, 1, 1, 0, 0))


class TestUpcoming(unittest.TestCase):
    def test_upcoming_daily(self):
        self.assertEqual(upcoming('@daily', datetime(2023, 1, 1, 12, 0), 3), [
            datetime(2023, 1, 2, 0, 0),
            datetime(2023, 1, 3, 0, 0),
            datetime(2023, 1, 4, 0, 0),
        ])

    def test_upcoming_every_hour(self):
        self.assertEqual(upcoming('0 * * * *', datetime(2023, 1, 1, 0, 0), 3), [
            datetime(2023, 1, 1, 1, 0),
            datetime(2023, 1, 1, 2, 0),
            datetime(2023, 1, 1, 3, 0),
        ])

    def test_upcoming_zero(self):
        self.assertEqual(upcoming('@daily', datetime(2023, 1, 1, 12, 0), 0), [])


class TestInvalid(unittest.TestCase):
    def _assert_value_error(self, expr, after=None):
        after = after or datetime(2023, 1, 1, 0, 0)
        with self.assertRaises(ValueError):
            next_run(expr, after)

    def test_wrong_field_count_too_few(self):
        self._assert_value_error('0 0 * *')

    def test_wrong_field_count_too_many(self):
        self._assert_value_error('0 0 * * * *')

    def test_out_of_range_minute(self):
        self._assert_value_error('60 * * * *')

    def test_out_of_range_hour(self):
        self._assert_value_error('0 24 * * *')

    def test_out_of_range_month(self):
        self._assert_value_error('0 * * 13 *')

    def test_out_of_range_day_of_week(self):
        self._assert_value_error('0 * * * 8')

    def test_out_of_range_day_of_month(self):
        self._assert_value_error('0 * * 32 *')

    def test_range_start_greater_than_end(self):
        self._assert_value_error('5-3 * * * *')

    def test_step_zero(self):
        self._assert_value_error('*/0 * * * *')

    def test_junk(self):
        self._assert_value_error('foo * * * *')

    def test_unknown_macro(self):
        self._assert_value_error('@bogus')

    def test_trailing_comma(self):
        self._assert_value_error('0, * * * *')

    def test_no_match_in_eight_years(self):
        # Feb 30 never exists.
        self._assert_value_error('0 0 30 2 *')


class TestEdgeCases(unittest.TestCase):
    def test_leap_year_feb29(self):
        # 2024 is a leap year.
        self.assertEqual(next_run('0 0 29 2 *', datetime(2023, 3, 1, 0, 0)),
                         datetime(2024, 2, 29, 0, 0))

    def test_step_field_max_dow(self):
        # 1/2 -> 1,3,5,7 (Mon/Wed/Fri/Sun). Jan 2 2023 is Monday.
        self.assertEqual(next_run('0 0 * * 1/2', datetime(2023, 1, 1, 0, 0)),
                         datetime(2023, 1, 2, 0, 0))

    def test_minute_step_full_range_dow(self):
        # 0/2 from 0 to 7 -> {0,2,4,6} (Sun/Tue/Thu/Sat).
        # Jan 3 2023 is a Tuesday, which precedes the Sunday on Jan 8.
        self.assertEqual(next_run('0 0 * * 0/2', datetime(2023, 1, 1, 12, 0)),
                         datetime(2023, 1, 3, 0, 0))


if __name__ == '__main__':
    unittest.main(verbosity=2)