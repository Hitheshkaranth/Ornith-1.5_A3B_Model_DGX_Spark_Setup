import unittest
from calendar_slots import free_slots, common_free, first_slot


class T(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(free_slots([("10:00", "11:00"), ("13:00", "14:30")]),
                         [("09:00", "10:00"), ("11:00", "13:00"), ("14:30", "17:00")])

    def test_empty(self): self.assertEqual(free_slots([]), [("09:00", "17:00")])

    def test_overlap_unsorted(self):
        self.assertEqual(free_slots([("13:00", "15:00"), ("9:30", "11:00"), ("10:30", "12:00")]),
                         [("09:00", "09:30"), ("12:00", "13:00"), ("15:00", "17:00")])

    def test_back_to_back(self):
        self.assertEqual(free_slots([("09:00", "10:00"), ("10:00", "12:00")]), [("12:00", "17:00")])

    def test_clip_outside_day(self):
        self.assertEqual(free_slots([("07:00", "09:45"), ("16:30", "19:00"), ("20:00", "21:00")]), [("09:45", "16:30")])

    def test_min_minutes(self):
        self.assertEqual(free_slots([("09:20", "12:00"), ("12:29", "16:00")], min_minutes=30), [("16:00", "17:00")])
        self.assertEqual(free_slots([("09:20", "12:00"), ("12:29", "16:00")], min_minutes=20),
                         [("09:00", "09:20"), ("12:00", "12:29"), ("16:00", "17:00")])

    def test_custom_day(self):
        self.assertEqual(free_slots([("23:00", "24:00")], day_start="0:00", day_end="24:00", min_minutes=60), [("00:00", "23:00")])

    def test_fully_busy(self): self.assertEqual(free_slots([("08:00", "18:00")]), [])

    def test_invalid(self):
        for b in [[("11:00", "10:00")], [("10:00", "10:00")], [("24:30", "25:00")], [("7:5", "8:00")], [("ab:cd", "10:00")], [("10:60", "11:00")]]:
            with self.subTest(b=b):
                with self.assertRaises(ValueError): free_slots(b)

    def test_common(self):
        a = [("09:00", "10:30"), ("12:00", "13:00")]
        b = [("10:00", "11:00"), ("15:00", "16:00")]
        self.assertEqual(common_free([a, b]), [("11:00", "12:00"), ("13:00", "15:00"), ("16:00", "17:00")])
        self.assertEqual(common_free([]), [("09:00", "17:00")])

    def test_first_slot(self):
        a = [("09:00", "10:30"), ("12:00", "13:00")]
        b = [("10:00", "11:00"), ("15:00", "16:00")]
        self.assertEqual(first_slot([a, b], 45), ("11:00", "11:45"))
        self.assertEqual(first_slot([a, b], 90), ("13:00", "14:30"))
        self.assertIsNone(first_slot([a, b], 150))
