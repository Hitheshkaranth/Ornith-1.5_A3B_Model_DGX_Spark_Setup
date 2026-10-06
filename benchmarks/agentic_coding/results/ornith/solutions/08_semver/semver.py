"""Semantic Versioning 2.0.0: parsing, precedence comparison, and ranges."""

import re

__all__ = ["parse", "compare", "satisfies"]

# Official SemVer 2.0.0 grammar.
_VERSION_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)"
    r"\.(?P<minor>0|[1-9]\d*)"
    r"\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>"
    r"(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*"
    r"))?"
    r"(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


def parse(v):
    """Parse a version string into (major, minor, patch, prerelease).

    `prerelease` is a tuple of dot-separated identifiers (empty tuple if none);
    build metadata is accepted and dropped. Raises ValueError if malformed.
    """
    if not isinstance(v, str):
        raise ValueError("version must be a string")
    m = _VERSION_RE.match(v)
    if not m:
        raise ValueError("invalid semantic version: %r" % (v,))
    prerelease = tuple(m.group("prerelease").split(".")) if m.group("prerelease") else ()
    return (int(m.group("major")), int(m.group("minor")), int(m.group("patch")), prerelease)


def _is_numeric(identifier):
    return identifier.isdigit()


def _compare_prerelease(a, b):
    for x, y in zip(a, b):
        x_num = _is_numeric(x)
        y_num = _is_numeric(y)
        if x_num and y_num:
            if int(x) != int(y):
                return -1 if int(x) < int(y) else 1
        elif x_num != y_num:
            # Numeric identifiers always have lower precedence than non-numeric.
            return -1 if x_num else 1
        elif x != y:
            return -1 if x < y else 1
    if len(a) != len(b):
        return -1 if len(a) < len(b) else 1
    return 0


def _cmp(pa, pb):
    """Compare two already-parsed version tuples; returns -1, 0, or 1."""
    for x, y in zip(pa[:3], pb[:3]):
        if x != y:
            return -1 if x < y else 1
    a_pre, b_pre = pa[3], pb[3]
    if a_pre and not b_pre:
        return -1
    if b_pre and not a_pre:
        return 1
    if a_pre or b_pre:
        return _compare_prerelease(a_pre, b_pre)
    return 0


def compare(a, b):
    """Compare two version strings by SemVer precedence. Returns -1, 0, or 1.

    Build metadata is ignored.
    """
    return _cmp(parse(a), parse(b))


def _compare_op(op, version, bound):
    c = _cmp(version, bound)
    if op == ">=":
        return c >= 0
    if op == "<=":
        return c <= 0
    if op == ">":
        return c > 0
    if op == "<":
        return c < 0
    if op == "=":
        return c == 0
    raise ValueError("unknown operator: %r" % (op,))


def _caret_upper(v):
    major, minor, patch, _ = v
    if major > 0:
        return (major + 1, 0, 0, ())
    if minor > 0:
        return (0, minor + 1, 0, ())
    return (0, 0, patch + 1, ())


def _tilde_upper(v):
    major, minor, patch, _ = v
    return (major, minor + 1, 0, ())


def _expand_comparator(token):
    """Return a list of (op, version_tuple) constraints for a comparator token."""
    token = token.strip()
    if token == "":
        raise ValueError("empty comparator")
    if token == "*":
        return [("star", None)]
    if token[0] in "=<>^~":
        i = 0
        while i < len(token) and token[i] in "=<>^~":
            i += 1
        op = token[:i]
        version = parse(token[i:].strip())
        if op == "^":
            return [(">=", version), ("<", _caret_upper(version))]
        if op == "~":
            return [(">=", version), ("<", _tilde_upper(version))]
        return [(op, version)]
    return [("=", parse(token))]


def _alternative_satisfies(version, alt):
    for token in alt.split():
        for op, bound in _expand_comparator(token):
            if op == "star":
                continue
            if not _compare_op(op, version, bound):
                return False
    return True


def satisfies(version, range):
    """Return whether `version` satisfies at least one alternative in `range`.

    An alternative is a set of whitespace-separated comparators that must all
    hold. Alternatives are separated by `||`. Raises ValueError if malformed.
    """
    v = parse(version)
    if not isinstance(range, str):
        raise ValueError("range must be a string")
    alternatives = range.split("||")
    if any(a.strip() == "" for a in alternatives):
        raise ValueError("malformed range: empty alternative")
    # Validate every comparator before short-circuit evaluation.
    for alt in alternatives:
        for token in alt.split():
            _expand_comparator(token)
    for alt in alternatives:
        if _alternative_satisfies(v, alt):
            return True
    return False