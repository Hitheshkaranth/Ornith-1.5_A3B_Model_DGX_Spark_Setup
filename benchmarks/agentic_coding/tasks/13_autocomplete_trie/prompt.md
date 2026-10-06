Create `autocomplete.py` with class `Autocomplete` (case-insensitive; all words are stored and returned lowercased):

- `add(word, weight=1)`: `word` must be a non-empty str and `weight` a positive int, else `ValueError`. Re-adding a word ADDS to its weight.
- `remove(word) -> bool`: remove the word; True if it existed.
- `weight(word) -> int`: current weight, 0 if absent.
- `suggest(prefix, k=5) -> list[str]`: up to `k` stored words starting with `prefix` (case-insensitive), sorted by weight
  descending, ties alphabetically ascending. Empty prefix considers all words. `k <= 0` returns `[]`.
- `__len__` (distinct words) and `__contains__`.
- Performance: with 100,000 words stored, thousands of `suggest()` calls with 3+ character prefixes must take well under a
  few seconds in total, so do not scan every word on each call (use a trie or similar index).
