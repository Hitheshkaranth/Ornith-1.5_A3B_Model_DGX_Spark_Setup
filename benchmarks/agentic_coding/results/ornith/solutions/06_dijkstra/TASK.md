Create `graph.py` with class `Graph` (weighted directed graph):

- `add_node(u)`: add an isolated node (no-op if present). Nodes are any hashable values.
- `add_edge(u, v, w, bidirectional=False)`: adds nodes as needed and an edge u->v with weight `w` (also v->u if bidirectional).
  Negative weight raises `ValueError`. If an edge u->v already exists keep the MINIMUM weight. Zero weights are allowed.
- `shortest_path(src, dst) -> tuple[cost, list]`: returns `(cost, [src, ..., dst])` for a minimum-cost path.
  If `src == dst` return `(0, [src])`. If `dst` is unreachable return `(math.inf, [])`.
  If `src` or `dst` is not a node of the graph raise `KeyError`.
