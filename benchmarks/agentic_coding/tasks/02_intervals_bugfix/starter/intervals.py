def merge_intervals(intervals):
    """Merge overlapping or touching closed intervals [start, end]."""
    result = []
    for iv in intervals:
        if result and iv[0] < result[-1][1]:
            result[-1][1] = max(result[-1][1], iv[1])
        else:
            result.append(iv)
    return result


def insert_interval(intervals, new):
    """Insert `new` into a list of intervals and merge."""
    out = []
    i = 0
    while i < len(intervals) and intervals[i][1] < new[0]:
        out.append(intervals[i])
        i += 1
    while i < len(intervals) and intervals[i][0] <= new[1]:
        new = [min(new[0], intervals[i][0]), max(new[1], intervals[i][1])]
        i += 1
    out.append(new)
    return out


def total_covered(intervals):
    """Total length covered by the union of the intervals."""
    return sum(e - s for s, e in intervals)
