import unittest

from calendar_slots import (
    _parse_time,
    _format_time,
    free_slots,
    common_free,
    first_slot,
)


class ParseTimeTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(_parse_time("9:00"), 540)
        self.assertEqual(_parse_time("09:00"), 540)
        self.assertEqual(_parse_time("0:00"), 0)
        self.assertEqual(_parse_time("24:00"), 1440)
        self.assertEqual(_parse_time("17:30"), 1050)

    def test_invalid(self):
        for bad in ["24:30", "7:5", "ab:cd", "", "9:", ":00", "9:000",
                    "100:00", "9:60", "-1:00", " 9:00", "9:00:00",
                    "1200", "09: ", "0a:00", " 09"]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    _parse_time(bad)


class FreeSlotsTests(unittest.TestCase):
    def test_no_busy(self):
        self.assertEqual(free_slots([]), [("09:00", "17:00")])

    def test_busy_in_middle(self):
        self.assertEqual(
            free_slots([("10:00", "11:00")]),
            [("09:00", "10:00"), ("11:00", "17:00")],
        )

    def test_min_minutes_equal_keeps(self):
        # (09:00,10:00) is exactly 60 min -> kept at threshold 60
        self.assertEqual(
            free_slots([("10:00", "11:00")], min_minutes=60),
            [("09:00", "10:00"), ("11:00", "17:00")],
        )

    def test_min_minutes_drops_small_gap(self):
        self.assertEqual(
            free_slots([("10:00", "11:00")], min_minutes=90),
            [("11:00", "17:00")],
        )

    def test_unsorted_and_overlapping(self):
        # busy (10:00,10:30),(11:00,13:00),(12:00,13:00) -> busy merges to
        # (10:00,10:30),(11:00,13:00); gaps: (9,10),(10:30,11),(13,17)
        self.assertEqual(
            free_slots([("12:00", "13:00"), ("11:00", "12:30"), ("10:00", "10:30")]),
            [("09:00", "10:00"), ("10:30", "11:00"), ("13:00", "17:00")],
        )

    def test_clipped_outside_day(self):
        self.assertEqual(
            free_slots([("08:00", "09:30"), ("16:30", "24:00")]),
            [("09:30", "16:30")],
        )

    def test_back_to_back_busy(self):
        self.assertEqual(
            free_slots([("09:00", "10:00"), ("10:00", "11:00")]),
            [("11:00", "17:00")],
        )

    def test_full_day_threshold(self):
        self.assertEqual(free_slots([], min_minutes=9 * 60), [])
        self.assertEqual(free_slots([], min_minutes=8 * 60), [("09:00", "17:00")])

    def test_gap_below_threshold_dropped(self):
        # free: (9:00,10:20)=80min, (14:00,17:00)=180min -> threshold 120 drops first
        self.assertEqual(
            free_slots([("10:20", "14:00")], min_minutes=120),
            [("14:00", "17:00")],
        )

    def test_bad_time_raises(self):
        with self.assertRaises(ValueError):
            free_slots([("24:30", "10:00")])

    def test_start_not_less_than_end(self):
        with self.assertRaises(ValueError):
            free_slots([("11:00", "11:00")])
        with self.assertRaises(ValueError):
            free_slots([("12:00", "11:00")])

    def test_custom_day(self):
        self.assertEqual(
            free_slots([("12:00", "13:00")], day_start="11:00", day_end="14:00"),
            [("11:00", "12:00"), ("13:00", "14:00")],
        )


class CommonFreeTests(unittest.TestCase):
    def test_two_calendars(self):
        # person1 free 9-10,11-17 ; person2 free 10:30-17 -> common 11-17
        self.assertEqual(
            common_free([[("10:00", "11:00")], [("09:00", "10:30")]]),
            [("11:00", "17:00")],
        )

    def test_disjoint_busy_no_common(self):
        self.assertEqual(
            common_free([[("09:00", "12:00")], [("12:00", "17:00")]]),
            [],
        )

    def test_min_minutes(self):
        self.assertEqual(
            common_free([[("10:00", "11:00")], [("10:00", "11:00")]], min_minutes=60),
            [("09:00", "10:00"), ("11:00", "17:00")],
        )

    def test_empty_calendars(self):
        self.assertEqual(common_free([]), [("09:00", "17:00")])

    def test_single_calendar(self):
        self.assertEqual(
            common_free([[("10:00", "11:00")]]),
            [("09:00", "10:00"), ("11:00", "17:00")],
        )

    def test_all_free_each_other(self):
        self.assertEqual(
            common_free([[("10:00", "12:00")], [("11:00", "13:00")]]),
            [("09:00", "10:00"), ("13:00", "17:00")],
        )

    def test_bad_block_raises(self):
        with self.assertRaises(ValueError):
            common_free([[("12:00", "11:00")], []])


class FirstSlotTests(unittest.TestCase):
    def test_earliest(self):
        self.assertEqual(
            first_slot([[("10:00", "11:00")]], 30),
            ("09:00", "09:30"),
        )

    def test_duration_fits_first_gap(self):
        # (9,10)=60<90; (11,17)>=90 -> (11:00,12:30)
        self.assertEqual(
            first_slot([[("10:00", "11:00")]], 90),
            ("11:00", "12:30"),
        )

    def test_none_when_too_small(self):
        # free: (9:30,10:00)=30min < 60 -> no slot
        self.assertIsNone(first_slot([[("09:00", "09:30"), ("10:00", "17:00")]], 60))

    def test_custom_start(self):
        self.assertEqual(
            first_slot([[("11:00", "12:00")]], 60, day_start="10:00", day_end="18:00"),
            ("10:00", "11:00"),
        )

    def test_common_earliest(self):
        self.assertEqual(
            first_slot([[("09:00", "10:00")], [("09:00", "10:00")]], 60),
            ("10:00", "11:00"),
        )

    def test_exactly_duration(self):
        self.assertEqual(
            first_slot([[("10:00", "11:00")]], 60),
            ("09:00", "10:00"),
        )

    def test_empty_calendars(self):
        self.assertEqual(
            first_slot([], 30),
            ("09:00", "09:30"),
        )


class FormatTests(unittest.TestCase):
    def test_padding(self):
        self.assertEqual(_format_time(0), "00:00")
        self.assertEqual(_format_time(540), "09:00")
        self.assertEqual(_format_time(1440), "24:00")


if __name__ == "__main__":
    unittest.main()
