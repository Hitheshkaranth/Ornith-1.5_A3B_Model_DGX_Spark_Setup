Create `deps.py` for a build system's dependency resolution.

Input `deps: dict[str, Iterable[str]]` maps each target to the targets it depends on (dependencies must be built first).
Nodes that only appear as dependencies are part of the graph too. Duplicate dependencies are allowed.

- Exception `CycleError(ValueError)` with attribute `cycle`: a list `[n0, n1, ..., nk, n0]` where each consecutive pair (x, y)
  means x depends on y (a self-dependency gives `['a', 'a']`).
- `build_order(deps) -> list[str]`: a valid build order containing every node; whenever several nodes are ready, pick the
  lexicographically smallest (so the result is deterministic). Raise `CycleError` if there is a cycle.
- `layers(deps) -> list[list[str]]`: layer 0 = nodes with no dependencies; a node is in layer k if its deepest dependency is in
  layer k-1. Each layer sorted. Raise `CycleError` on cycles.
- `affected(deps, changed) -> set[str]`: the changed nodes plus every node that transitively depends on any of them.
- Must handle graphs with 10,000+ nodes and dependency chains thousands of nodes deep (including long cycles) without hitting
  Python's recursion limit.
