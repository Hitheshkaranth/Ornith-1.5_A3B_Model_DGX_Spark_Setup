import math
import heapq


class Graph:
    def __init__(self):
        self._neighbors = {}

    def add_node(self, u):
        if u not in self._neighbors:
            self._neighbors[u] = {}

    def add_edge(self, u, v, w, bidirectional=False):
        if w < 0:
            raise ValueError("negative weight not allowed")
        self.add_node(u)
        self.add_node(v)
        if v not in self._neighbors[u] or w < self._neighbors[u][v]:
            self._neighbors[u][v] = w
        if bidirectional:
            if u not in self._neighbors[v] or w < self._neighbors[v][u]:
                self._neighbors[v][u] = w

    def shortest_path(self, src, dst):
        if src not in self._neighbors:
            raise KeyError(src)
        if dst not in self._neighbors:
            raise KeyError(dst)
        if src == dst:
            return (0, [src])

        dist = {src: 0}
        prev = {}
        visited = set()
        heap = [(0, src)]
        while heap:
            d, u = heapq.heappop(heap)
            if u in visited:
                continue
            visited.add(u)
            if u == dst:
                break
            for v, w in self._neighbors[u].items():
                if v in visited:
                    continue
                nd = d + w
                if v not in dist or nd < dist[v]:
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(heap, (nd, v))

        if dst not in dist:
            return (math.inf, [])

        path = []
        cur = dst
        while cur != src:
            path.append(cur)
            cur = prev[cur]
        path.append(src)
        path.reverse()
        return (dist[dst], path)


if __name__ == "__main__":
    import unittest
    unittest.main()