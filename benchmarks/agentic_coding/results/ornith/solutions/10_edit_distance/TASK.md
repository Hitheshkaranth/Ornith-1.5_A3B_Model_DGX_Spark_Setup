Create `editdist.py`:

- `levenshtein(a: str, b: str) -> int`: minimum number of single-character insertions, deletions and substitutions.
- `alignment(a: str, b: str) -> list[tuple]`: an optimal edit script as a list of ops, in order, that transforms `a` into `b`:
  `('keep', ch)`, `('sub', old_ch, new_ch)`, `('ins', ch)`, `('del', ch)`. Applying the ops left to right while walking
  through `a` must produce `b`, and the number of non-`keep` ops must equal `levenshtein(a, b)`.
- `osa_distance(a: str, b: str) -> int`: optimal string alignment distance = Levenshtein plus transposition of two ADJACENT
  characters at cost 1, where no substring is edited more than once (e.g. `osa_distance("ca", "abc") == 3`, `osa_distance("ab", "ba") == 1`).
- `closest(word: str, candidates: list[str], max_distance: int | None = None) -> list[str]`: the candidates having the minimal
  Levenshtein distance to `word`, in their original order; candidates farther than `max_distance` are excluded; `[]` if none qualify.
- Must handle two 1000-character strings in a few seconds.
