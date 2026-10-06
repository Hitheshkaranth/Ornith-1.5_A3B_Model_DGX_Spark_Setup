Create `rematch.py`, a small regular-expression engine. Do NOT import or use the `re` module.

- `fullmatch(pattern, text) -> bool`: the whole text must match.
- `search(pattern, text) -> bool`: some substring matches.

Pattern syntax:
- Literal characters; `.` matches any single character.
- Character classes `[abc]`, ranges `[a-z0-9]`, negated `[^...]`. Inside a class `\` escapes the next character.
- `\` outside a class makes the next character literal (e.g. `\.`, `\*`, `\[`, `\\`).
- Quantifiers `*`, `+`, `?` apply to the single preceding atom (char, `.`, or class). No groups or alternation.
- In `search`, a leading `^` anchors to the start and a trailing `$` anchors to the end of text. (`fullmatch` accepts them too, with no effect.)
- Invalid patterns raise `ValueError`: a quantifier with nothing to repeat (`*a`, `+`), stacked quantifiers (`a**`, `a+?`, `a?*`),
  an unterminated class (`[abc`), a reversed range (`[z-a]`), or a trailing lone backslash.
- Must not blow up exponentially: e.g. `fullmatch("a*a*a*a*a*a*a*a*b", "a" * 40)` must return False quickly.
