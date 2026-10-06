import heapq
import math


class Graph:
    def __init__(self):
        self.adj = {}

    def add_node(self, u):
        self.adj.setdefault(u, {})

    def add_edge(self, u, v, w, bidirectional=False):
        if w < 0:
            raise ValueError("negative weight")
        self.add_node(u); self.add_node(v)
        if w < self.adj[u].get(v, math.inf):
            self.adj[u][v] = w
        if bidirectional and w < self.adj[v].get(u, math.inf):
            self.adj[v][u] = w

    def shortest_path(self, src, dst):
        if src not in self.adj or dst not in self.adj:
            raise KeyError(src if src not in self.adj else dst)
        dist, prev, done = {src: 0}, {}, set()
        pq, cnt = [(0, 0, src)], 1
        while pq:
            d, _, u = heapq.heappop(pq)
            if u in done:
                continue
            done.add(u)
            if u == dst:
                break
            for v, w in self.adj[u].items():
                nd = d + w
                if v not in dist or nd < dist[v]:
                    dist[v] = nd; prev[v] = u
                    heapq.heappush(pq, (nd, cnt, v)); cnt += 1
        if dst not in dist:
            return (math.inf, [])
        path = [dst]
        while path[-1] != src:
            path.append(prev[path[-1]])
        return (dist[dst], path[::-1])
