"""Edit-distance utilities: Levenshtein, optimal alignment script, and OSA."""


def levenshtein(a: str, b: str) -> int:
    """Minimum number of single-character insertions, deletions and substitutions
    to transform ``a`` into ``b``."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    # Guarantee len(b) is the smaller dimension so we keep two rows minimal.
    if len(a) < len(b):
        a, b = b, a

    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            current.append(min(
                previous[j] + 1,       # deletion
                current[j - 1] + 1,    # insertion
                previous[j - 1] + cost,  # substitution
            ))
        previous = current
    return previous[-1]


def alignment(a: str, b: str) -> list[tuple]:
    """An optimal edit script transforming ``a`` into ``b``.

    Each op is one of ``('keep', ch)``, ``('sub', old, new)``,
    ``('ins', ch)`` or ``('del', ch)``. Applying them left-to-right while
    walking through ``a`` yields ``b``; the number of non-``keep`` ops equals
    :func:`levenshtein` (a, b).
    """
    n, m = len(a), len(b)
    if n == 0 or m == 0:
        ops = []
        for ch in b:
            ops.append(('ins', ch))
        for ch in a:
            ops.append(('del', ch))
        return ops

    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        ca = a[i - 1]
        row = dp[i]
        prev = dp[i - 1]
        for j in range(1, m + 1):
            cost = 0 if ca == b[j - 1] else 1
            row[j] = min(
                prev[j] + 1,
                row[j - 1] + 1,
                prev[j - 1] + cost,
            )

    ops = []
    i, j = n, m
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            ops.append(('keep', a[i - 1]))
            i -= 1
            j -= 1
        elif dp[i][j] == dp[i - 1][j - 1] + 1:
            ops.append(('sub', a[i - 1], b[j - 1]))
            i -= 1
            j -= 1
        elif dp[i][j] == dp[i - 1][j] + 1:
            ops.append(('del', a[i - 1]))
            i -= 1
        else:
            ops.append(('ins', b[j - 1]))
            j -= 1
    while i > 0:
        ops.append(('del', a[i - 1]))
        i -= 1
    while j > 0:
        ops.append(('ins', b[j - 1]))
        j -= 1
    ops.reverse()
    return ops


def _apply(ops: list[tuple]) -> str:
    out = []
    for op in ops:
        if op[0] == 'keep':
            out.append(op[1])
        elif op[0] == 'sub':
            out.append(op[2])
        elif op[0] == 'ins':
            out.append(op[1])
        elif op[0] == 'del':
            pass
    return ''.join(out)


def osa_distance(a: str, b: str) -> int:
    """Optimal string alignment distance: Levenshtein plus transposition of two
    adjacent characters at cost 1, with no substring edited more than once."""
    n, m = len(a), len(b)
    if n == 0:
        return m
    if m == 0:
        return n

    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j

    for i in range(1, n + 1):
        ca = a[i - 1]
        a_prev = a[i - 2] if i >= 2 else ''
        row = d[i]
        prev = d[i - 1]
        for j in range(1, m + 1):
            cb = b[j - 1]
            cost = 0 if ca == cb else 1
            best = min(
                prev[j] + 1,      # deletion
                row[j - 1] + 1,   # insertion
                prev[j - 1] + cost,  # substitution
            )
            if i >= 2 and j >= 2 and ca == b[j - 2] and a_prev == cb:
                sub = d[i - 2][j - 2] + cost
                if sub < best:
                    best = sub
            row[j] = best
    return d[n][m]


def closest(word: str, candidates: list[str], max_distance: int | None = None) -> list[str]:
    """Return candidates with the minimal Levenshtein distance to ``word`` in
    their original order. Candidates farther than ``max_distance`` are excluded;
    returns ``[]`` if none qualify."""
    if not candidates:
        return []

    scored = [(c, levenshtein(word, c)) for c in candidates]
    min_distance = min(dist for _, dist in scored)

    result = []
    for candidate, dist in scored:
        if dist != min_distance:
            continue
        if max_distance is not None and dist > max_distance:
            continue
        result.append(candidate)
    return result


if __name__ == '__main__':
    assert levenshtein('ca', 'abc') == 3
    assert levenshtein('kitten', 'sitting') == 3
    assert osa_distance('ca', 'abc') == 3
    assert osa_distance('ab', 'ba') == 1
    assert levenshtein('', 'abc') == 3
    assert levenshtein('abc', 'abc') == 0

    script = alignment('kitten', 'sitting')
    assert _apply(script) == 'sitting'
    assert sum(1 for op in script if op[0] != 'keep') == 3

    assert closest('cat', ['car', 'cot', 'dog', 'bat'], max_distance=2) == ['car', 'cot', 'bat']
    assert closest('cat', ['zzzz', 'yyyy']) == ['zzzz', 'yyyy']
    assert closest('abc', ['abc', 'abd', 'xyz']) == ['abc']
    print('All quick checks passed.')