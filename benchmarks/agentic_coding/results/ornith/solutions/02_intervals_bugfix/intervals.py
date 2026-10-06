def _validate(interval):
    start, end = interval[0], interval[1]
    if start > end:
        raise ValueError(
            f"Interval must satisfy start <= end, got [{start}, {end}]"
        )
    return [start, end]


def merge_intervals(intervals):
    """Merge overlapping or touching closed intervals [start, end]."""
    result = []
    for iv in sorted((_validate(iv) for iv in intervals), key=lambda x: x[0]):
        if result and iv[0] <= result[-1][1]:
            result[-1][1] = max(result[-1][1], iv[1])
        else:
            result.append(iv)
    return result


def insert_interval(intervals, new):
    """Insert `new` into a list of intervals and merge."""
    return merge_intervals(list(intervals) + [_validate(new)])


def total_covered(intervals):
    """Total length covered by the union of the intervals."""
    return sum(e - s for s, e in merge_intervals(intervals))