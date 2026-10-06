Create `semver.py` implementing Semantic Versioning 2.0.0 parsing, comparison and ranges.

- `parse(v: str) -> tuple`: returns `(major, minor, patch, prerelease)` where `prerelease` is a tuple of the dot-separated
  prerelease identifiers as strings (empty tuple if none). Build metadata (`+...`) is accepted and dropped.
  Example: `parse("1.2.3-alpha.1+build.5") == (1, 2, 3, ("alpha", "1"))`.
  Invalid versions raise `ValueError`: must be exactly `X.Y.Z` with no leading zeros in numeric parts, no `v` prefix,
  prerelease identifiers non-empty, numeric prerelease identifiers without leading zeros.
- `compare(a: str, b: str) -> int`: -1, 0 or 1 following SemVer precedence rules (prerelease < release; identifiers compared
  numerically when both numeric, numeric < alphanumeric, else ASCII order; a shorter prefix set has lower precedence).
  Build metadata is ignored.
- `satisfies(version: str, range: str) -> bool`:
  * A range is one or more alternatives separated by `||`; an alternative is one or more whitespace-separated comparators that must ALL hold.
  * Comparators: `>=V`, `>V`, `<=V`, `<V`, `=V`, bare `V` (exact), `^V`, `~V`, and `*` (matches anything). V is always a full X.Y.Z[-pre].
  * Caret: `^1.2.3` := `>=1.2.3 <2.0.0`; `^0.2.3` := `>=0.2.3 <0.3.0`; `^0.0.3` := `>=0.0.3 <0.0.4`.
  * Tilde: `~1.2.3` := `>=1.2.3 <1.3.0`.
  * Use plain `compare` semantics (no special prerelease exclusion rules).
  * A malformed range (empty, bad version in a comparator) raises `ValueError`.
