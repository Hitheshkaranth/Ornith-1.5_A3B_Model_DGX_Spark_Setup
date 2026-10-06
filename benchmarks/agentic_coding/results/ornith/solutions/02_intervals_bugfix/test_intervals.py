import unittest

import intervals as m


class MergeIntervalTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(m.merge_intervals([]), [])

    def test_single(self):
        self.assertEqual(m.merge_intervals([[1, 3]]), [[1, 3]])

    def test_sorted_no_overlap(self):
        self.assertEqual(m.merge_intervals([[1, 2], [4, 5]]), [[1, 2], [4, 5]])

    def test_unsorted(self):
        self.assertEqual(m.merge_intervals([[4, 5], [1, 3]]), [[1, 3], [4, 5]])

    def test_overlapping(self):
        self.assertEqual(m.merge_intervals([[1, 4], [2, 6]]), [[1, 6]])

    def test_touching(self):
        self.assertEqual(m.merge_intervals([[1, 3], [3, 5]]), [[1, 5]])

    def test_touching_unsorted(self):
        self.assertEqual(m.merge_intervals([[3, 5], [1, 3]]), [[1, 5]])

    def test_complex(self):
        inp = [[1, 3], [8, 10], [2, 6], [15, 18]]
        self.assertEqual(m.merge_intervals(inp), [[1, 6], [8, 10], [15, 18]])

    def test_does_not_mutate_input(self):
        inp = [[1, 3], [2, 6]]
        backup = [list(x) for x in inp]
        m.merge_intervals(inp)
        self.assertEqual(inp, backup)

    def test_returns_copies(self):
        inp = [[1, 6]]
        out = m.merge_intervals(inp)
        out[0][0] = 99
        self.assertEqual(inp, [[1, 6]])

    def test_all_merge(self):
        self.assertEqual(m.merge_intervals([[1, 4], [3, 7], [2, 5]]), [[1, 7]])


class InsertIntervalTests(unittest.TestCase):
    def test_simple_insert(self):
        self.assertEqual(m.insert_interval([[1, 2], [5, 6]], [3, 4]),
                         [[1, 2], [3, 4], [5, 6]])

    def test_merges_into_existing(self):
        self.assertEqual(m.insert_interval([[1, 4], [5, 8]], [3, 6]),
                         [[1, 8]])

    def test_touching_insert(self):
        self.assertEqual(m.insert_interval([[1, 3]], [3, 5]), [[1, 5]])

    def test_unsorted_input(self):
        self.assertEqual(m.insert_interval([[5, 6], [1, 3]], [2, 4]),
                         [[1, 4], [5, 6]])

    def test_overlapping_input(self):
        self.assertEqual(m.insert_interval([[1, 4], [2, 5]], [6, 7]),
                         [[1, 5], [6, 7]])

    def test_matches_merge_add(self):
        cases = [
            ([[1, 3], [8, 10], [2, 6], [15, 18]], [4, 7]),
            ([[10, 15], [1, 3]], [3, 12]),
            ([[0, 0], [5, 5]], [4, 6]),
        ]
        for base, new in cases:
            self.assertEqual(m.insert_interval(base, new),
                             m.merge_intervals(list(base) + [new]))

    def test_does_not_mutate(self):
        base = [[1, 4], [5, 8]]
        new = [3, 6]
        base_backup = [list(x) for x in base]
        new_backup = list(new)
        m.insert_interval(base, new)
        self.assertEqual(base, base_backup)
        self.assertEqual(new, new_backup)


class TotalCoveredTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(m.total_covered([]), 0)

    def test_simple(self):
        self.assertEqual(m.total_covered([[1, 4]]), 3)

    def test_overlap_counted_once(self):
        self.assertEqual(m.total_covered([[1, 4], [2, 6]]), 5)

    def test_touching(self):
        self.assertEqual(m.total_covered([[1, 3], [3, 5]]), 4)

    def test_disjoint(self):
        self.assertEqual(m.total_covered([[1, 2], [5, 8]]), 4)

    def test_unsorted(self):
        self.assertEqual(m.total_covered([[5, 8], [1, 2]]), 4)


class ValueErrorTests(unittest.TestCase):
    def test_bad_in_merge(self):
        with self.assertRaises(ValueError):
            m.merge_intervals([[3, 1]])

    def test_bad_in_total(self):
        with self.assertRaises(ValueError):
            m.total_covered([[5, 2]])

    def test_bad_in_insert(self):
        with self.assertRaises(ValueError):
            m.insert_interval([[1, 3]], [5, 2])

    def test_valid_boundary_ok(self):
        self.assertEqual(m.merge_intervals([[2, 2]]), [[2, 2]])


if __name__ == "__main__":
    unittest.main(verbosity=2)