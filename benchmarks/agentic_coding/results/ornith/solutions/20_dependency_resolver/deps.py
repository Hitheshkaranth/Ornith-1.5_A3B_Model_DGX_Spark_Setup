"""Dependency resolution for a build system.

The public API:
    CycleError   - raised (as ValueError) when the dependency graph has a cycle
    build_order  - deterministic topological order (lexicographically smallest)
    layers       - dependency depth layers
    affected     - transitive impact set of changed nodes

All routines are fully iterative so they work for very large graphs and very
deep chains/cycles without hitting Python's recursion limit.
"""

import heapq


class CycleError(ValueError):
    """Raised when the dependency graph contains a cycle.

    The ``cycle`` attribute is a list ``[n0, n1, ..., nk, n0]`` where every
    consecutive pair ``(x, y)`` means that ``x`` depends on ``y``.
    """

    def __init__(self, cycle):
        self.cycle = list(cycle)
        message = "dependency cycle detected: " + " -> ".join(str(n) for n in self.cycle)
        super().__init__(message)


def _graph(deps):
    """Normalise ``deps`` into shared structures.

    Returns ``(nodes, deps_map, dependents)`` where:
        nodes       - set of every node (keys and dependency-only nodes)
        deps_map    - node -> set of nodes it depends on (deps only as deps: empty)
        dependents  - node -> set of nodes that depend on it (reverse edges)
    """
    nodes = set()
    deps_map = {}
    for target, deps_iter in deps.items():
        nodes.add(target)
        ds = set()
        for dep in deps_iter:
            ds.add(dep)
            nodes.add(dep)
        deps_map[target] = ds

    for node in nodes:
        deps_map.setdefault(node, frozenset())

    dependents = {node: set() for node in nodes}
    for target, ds in deps_map.items():
        for dep in ds:
            dependents[dep].add(target)

    return nodes, deps_map, dependents


def _find_cycle(deps_map):
    """Iterative DFS that returns a cycle (list of nodes) or ``None``.

    Edges point from a node to its dependencies, so a cycle here is a real
    dependency cycle. Iteration over dependencies is sorted so the result is
    deterministic.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in deps_map}

    for root in deps_map:
        if color[root] != WHITE:
            continue

        color[root] = GRAY
        stack = [(root, iter(deps_map[root]))]
        path = [root]

        while stack:
            node, children = stack[-1]
            stepped = False
            for dep in children:
                state = color[dep]
                if state == WHITE:
                    color[dep] = GRAY
                    path.append(dep)
                    stack.append((dep, iter(deps_map[dep])))
                    stepped = True
                    break
                if state == GRAY:
                    start = path.index(dep)
                    return path[start:] + [dep]
            if not stepped:
                color[node] = BLACK
                stack.pop()
                path.pop()

    return None


def _topological_order(deps):
    """Kahn's algorithm with a min-heap for the lex-smallest order.

    Returns ``(order, deps_map, nodes)`` or raises :class:`CycleError`.
    """
    nodes, deps_map, dependents = _graph(deps)
    remaining = {node: len(deps_map[node]) for node in nodes}

    heap = [node for node in nodes if remaining[node] == 0]
    heapq.heapify(heap)

    order = []
    while heap:
        node = heapq.heappop(heap)
        order.append(node)
        for dependent in sorted(dependents[node]):
            remaining[dependent] -= 1
            if remaining[dependent] == 0:
                heapq.heappush(heap, dependent)

    if len(order) != len(nodes):
        cycle = _find_cycle(deps_map)
        raise CycleError(cycle)

    return order, deps_map, nodes


def build_order(deps):
    """Return a valid build order (every node) with lexicographically smallest
    tie-breaking. Raises :class:`CycleError` on cycles."""
    order, _, _ = _topological_order(deps)
    return order


def layers(deps):
    """Return dependency-depth layers.

    Layer 0 = nodes with no dependencies; a node sits in layer ``k`` when its
    deepest dependency is in layer ``k-1``. Each layer is sorted.
    Raises :class:`CycleError` on cycles.
    """
    order, deps_map, nodes = _topological_order(deps)

    depth = {}
    for node in order:
        deps_of = deps_map[node]
        if deps_of:
            depth[node] = 1 + max(depth[dep] for dep in deps_of)
        else:
            depth[node] = 0

    max_depth = max(depth.values(), default=-1)
    buckets = []
    for level in range(max_depth + 1):
        buckets.append(sorted(node for node in nodes if depth[node] == level))
    return buckets


def affected(deps, changed):
    """Return the changed nodes plus every node that transitively depends on
    any of them."""
    _, _, dependents = _graph(deps)

    result = set()
    stack = list(changed)
    while stack:
        node = stack.pop()
        if node in result:
            continue
        result.add(node)
        for dependent in dependents.get(node, ()):
            if dependent not in result:
                stack.append(dependent)
    return result