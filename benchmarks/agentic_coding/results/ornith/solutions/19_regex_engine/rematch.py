"""A small regular-expression engine.

Supports: literals, ``.`` (any char), character classes with ranges and
negation, backslash escapes, and the ``*`` ``+`` ``?`` quantifiers.
No groups, no alternation.

``fullmatch`` requires the whole text to match; ``search`` looks for any
matching substring.  In ``search`` a leading ``^`` anchors to the start and a
trailing ``$`` anchors to the end of the text.

The matcher is memoized, so it runs in polynomial time and never blows up
exponentially.
"""

import sys

__all__ = ["fullmatch", "search"]

# Atom depth equals the number of pattern atoms; keep the ceiling generous so
# moderately long patterns still match.
try:
    sys.setrecursionlimit(100000)
except (ValueError, OverflowError):
    pass

_MISSING = object()


def _char_match(ch):
    return lambda c: c == ch


def _any_match(c):
    return True


def _make_class_test(chars, ranges, negated):
    def test(c):
        in_class = c in chars
        if not in_class:
            for s, e in ranges:
                if s <= c <= e:
                    in_class = True
                    break
        return (not in_class) if negated else in_class

    return test


def _parse(pattern):
    """Parse ``pattern`` into atoms.

    Returns ``(atoms, anchor_start, anchor_end)`` where each atom is a
    ``(matcher, quantifier)`` pair.  ``quantifier`` is one of ``'1'``, ``'*'``,
    ``'+'`` or ``'?'``.
    """
    n = len(pattern)
    i = 0
    atoms = []
    anchor_start = False
    anchor_end = False

    def parse_class(start):
        j = start + 1
        negated = False
        if j < n and pattern[j] == "^":
            negated = True
            j += 1
        chars = set()
        ranges = []
        while j < n and pattern[j] != "]":
            if pattern[j] == "\\":
                if j + 1 >= n:
                    raise ValueError("trailing backslash in class")
                ch = pattern[j + 1]
                k = j + 2
            else:
                ch = pattern[j]
                k = j + 1
            if k < n and pattern[k] == "-" and k + 1 < n and pattern[k + 1] != "]":
                if pattern[k + 1] == "\\":
                    if k + 2 >= n:
                        raise ValueError("trailing backslash in class")
                    end_ch = pattern[k + 2]
                    m = k + 3
                else:
                    end_ch = pattern[k + 1]
                    m = k + 2
                if ch > end_ch:
                    raise ValueError("reversed range in class")
                ranges.append((ch, end_ch))
                j = m
            else:
                chars.add(ch)
                j = k
        if j >= n:
            raise ValueError("unterminated character class")
        return _make_class_test(chars, ranges, negated), j + 1

    while i < n:
        c = pattern[i]
        if c in "*+?":
            raise ValueError("nothing to repeat")
        if c == "^" and i == 0:
            anchor_start = True
            i += 1
            continue
        if c == "$" and i == n - 1:
            anchor_end = True
            i += 1
            continue
        if c == "[":
            matcher, i = parse_class(i)
        elif c == ".":
            matcher = _any_match
            i += 1
        elif c == "\\":
            if i + 1 >= n:
                raise ValueError("trailing lone backslash")
            matcher = _char_match(pattern[i + 1])
            i += 2
        else:
            matcher = _char_match(c)
            i += 1

        if i < n and pattern[i] in "*+?":
            if i + 1 < n and pattern[i + 1] in "*+?":
                raise ValueError("stacked quantifier")
            quant = pattern[i]
            i += 1
        else:
            quant = "1"
        atoms.append((matcher, quant))

    return atoms, anchor_start, anchor_end


def _compile(pattern):
    if not isinstance(pattern, str):
        raise TypeError("expected string, got %s" % type(pattern).__name__)
    return _parse(pattern)


def _make_matcher(atoms, text, need_end):
    n_atoms = len(atoms)
    n_text = len(text)
    memo = {}

    def match(i, j):
        if i == n_atoms:
            return (j == n_text) if need_end else True
        key = (i, j)
        cached = memo.get(key, _MISSING)
        if cached is not _MISSING:
            return cached
        result = compute(i, j)
        memo[key] = result
        return result

    def compute(i, j):
        matcher, quant = atoms[i]
        if quant == "1":
            if j < n_text and matcher(text[j]):
                return match(i + 1, j + 1)
            return False
        if quant == "?":
            if match(i + 1, j):
                return True
            if j < n_text and matcher(text[j]) and match(i + 1, j + 1):
                return True
            return False
        if quant == "*":
            k = 0
            while True:
                if match(i + 1, j + k):
                    return True
                if j + k < n_text and matcher(text[j + k]):
                    k += 1
                else:
                    return False
        # quant == "+"
        if j < n_text and matcher(text[j]):
            k = 1
            while True:
                if match(i + 1, j + k):
                    return True
                if j + k < n_text and matcher(text[j + k]):
                    k += 1
                else:
                    return False
        return False

    return match


def fullmatch(pattern, text):
    if not isinstance(text, str):
        raise TypeError("expected string, got %s" % type(text).__name__)
    atoms, _anchor_start, _anchor_end = _compile(pattern)
    match = _make_matcher(atoms, text, need_end=True)
    return match(0, 0)


def search(pattern, text):
    if not isinstance(text, str):
        raise TypeError("expected string, got %s" % type(text).__name__)
    atoms, anchor_start, anchor_end = _compile(pattern)
    match = _make_matcher(atoms, text, need_end=anchor_end)
    if anchor_start:
        return match(0, 0)
    for start in range(len(text) + 1):
        if match(0, start):
            return True
    return False