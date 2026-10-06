import unittest, copy
from intervals import merge_intervals, insert_interval, total_covered


class T(unittest.TestCase):
    def test_basic(self): self.assertEqual(merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]), [[1, 6], [8, 10], [15, 18]])
    def test_unsorted(self): self.assertEqual(merge_intervals([[8, 10], [1, 3], [2, 6]]), [[1, 6], [8, 10]])
    def test_touching(self): self.assertEqual(merge_intervals([[1, 3], [3, 5]]), [[1, 5]])
    def test_contained(self): self.assertEqual(merge_intervals([[1, 10], [2, 3], [4, 5]]), [[1, 10]])

    def test_no_mutation(self):
        data = [[1, 3], [2, 6]]; snap = copy.deepcopy(data); merge_intervals(data); self.assertEqual(data, snap)

    def test_result_not_aliased(self):
        data = [[1, 3]]; out = merge_intervals(data); out[0][1] = 99; self.assertEqual(data, [[1, 3]])

    def test_tuples_input(self): self.assertEqual(merge_intervals([(5, 6), (1, 2)]), [[1, 2], [5, 6]])

    def test_empty(self):
        self.assertEqual(merge_intervals([]), []); self.assertEqual(total_covered([]), 0)

    def test_invalid(self):
        with self.assertRaises(ValueError): merge_intervals([[3, 1]])

    def test_insert_middle(self):
        self.assertEqual(insert_interval([[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8]), [[1, 2], [3, 10], [12, 16]])

    def test_insert_keeps_tail(self): self.assertEqual(insert_interval([[1, 2], [10, 12]], [4, 5]), [[1, 2], [4, 5], [10, 12]])
    def test_insert_unsorted(self): self.assertEqual(insert_interval([[10, 12], [1, 2]], [2, 4]), [[1, 4], [10, 12]])

    def test_insert_no_mutation(self):
        data = [[1, 2], [5, 6]]; insert_interval(data, [2, 5]); self.assertEqual(data, [[1, 2], [5, 6]])

    def test_total(self): self.assertEqual(total_covered([[1, 3], [2, 6], [10, 11]]), 6)
    def test_total_float(self): self.assertAlmostEqual(total_covered([[0.5, 1.5], [1.0, 2.0]]), 1.5)
