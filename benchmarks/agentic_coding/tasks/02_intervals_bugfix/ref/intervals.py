def merge_intervals(intervals):
    ivs = []
    for s, e in intervals:
        if s > e:
            raise ValueError("start > end")
        ivs.append([s, e])
    ivs.sort()
    out = []
    for s, e in ivs:
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out


def insert_interval(intervals, new):
    return merge_intervals(list(intervals) + [new])


def total_covered(intervals):
    return sum(e - s for s, e in merge_intervals(intervals))
