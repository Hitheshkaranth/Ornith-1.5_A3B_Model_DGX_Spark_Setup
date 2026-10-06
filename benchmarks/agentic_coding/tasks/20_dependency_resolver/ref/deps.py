import heapq


class CycleError(ValueError):
    def __init__(self, cycle):
        super().__init__("cycle: " + " -> ".join(cycle))
        self.cycle = cycle


def _graph(deps):
    g = {}
    for k, vs in deps.items():
        g.setdefault(k, set())
        for v in vs:
            g[k].add(v); g.setdefault(v, set())
    return g


def _find_cycle(g, nodes):
    color = {}
    for start in sorted(nodes):
        if color.get(start):
            continue
        stack = [(start, iter(sorted(g[start])))]; path = [start]; color[start] = 1
        while stack:
            u, it = stack[-1]
            nxt = next(it, None)
            if nxt is None:
                stack.pop(); path.pop(); color[u] = 2; continue
            if nxt not in nodes:
                continue
            c = color.get(nxt)
            if c == 1:
                i = path.index(nxt); return path[i:] + [nxt]
            if c is None:
                color[nxt] = 1; path.append(nxt); stack.append((nxt, iter(sorted(g[nxt]))))
    return None


def _kahn(deps):
    g = _graph(deps)
    rdeps = {n: [] for n in g}
    indeg = {n: len(g[n]) for n in g}
    for n, ds in g.items():
        for d in ds:
            rdeps[d].append(n)
    return g, rdeps, indeg


def build_order(deps):
    g, rdeps, indeg = _kahn(deps)
    ready = [n for n, d in indeg.items() if d == 0]; heapq.heapify(ready)
    out = []
    while ready:
        n = heapq.heappop(ready); out.append(n)
        for m in rdeps[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                heapq.heappush(ready, m)
    if len(out) != len(g):
        raise CycleError(_find_cycle(g, {n for n in g if indeg[n] > 0}))
    return out


def layers(deps):
    g, rdeps, indeg = _kahn(deps)
    cur = sorted(n for n, d in indeg.items() if d == 0); out = []; seen = 0
    while cur:
        out.append(cur); seen += len(cur); nxt = []
        for n in cur:
            for m in rdeps[n]:
                indeg[m] -= 1
                if indeg[m] == 0:
                    nxt.append(m)
        cur = sorted(nxt)
    if seen != len(g):
        raise CycleError(_find_cycle(g, {n for n in g if indeg[n] > 0}))
    return out


def affected(deps, changed):
    g, rdeps, _ = _kahn(deps)
    res = set(changed); stack = list(res)
    while stack:
        n = stack.pop()
        for m in rdeps.get(n, ()):
            if m not in res:
                res.add(m); stack.append(m)
    return res
