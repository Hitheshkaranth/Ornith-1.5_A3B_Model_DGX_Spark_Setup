Users report wrong results from `intervals.py`. Find and fix all the bugs. Required behaviour:

- Intervals are `[start, end]` pairs (lists or tuples) of numbers with `start <= end`. Any interval with `start > end` raises `ValueError`.
- `merge_intervals(intervals)`: input may be in any order. Overlapping OR touching intervals (`[1,3]` and `[3,5]`) are merged.
  Returns a NEW list of `[start, end]` lists sorted by start. It must never mutate its input (nor the inner lists).
- `insert_interval(intervals, new)`: `intervals` may be unsorted/overlapping. Returns exactly what `merge_intervals(intervals + [new])` would. Must not mutate inputs.
- `total_covered(intervals)`: total length of the union of the intervals (overlaps counted once).
- Empty input: `merge_intervals([]) == []`, `total_covered([]) == 0`.
