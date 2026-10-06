Create `minijson.py` with `loads(s: str)` — a strict JSON (RFC 8259) parser. Do NOT use the `json` module.

- Return Python values exactly like `json.loads` would: dict (later duplicate keys win, key order preserved), list, str, int
  (for numbers without fraction/exponent), float (otherwise), True, False, None.
- Strings: escapes `\" \\ \/ \b \f \n \r \t \uXXXX`; a `\uXXXX` high surrogate followed by a `\uXXXX` low surrogate combines
  into one code point. Raw control characters (< U+0020) inside strings are invalid.
- Numbers: `-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?` only (no leading `+`, no leading zeros, no `.5`, no `1.`, no hex, no NaN/Infinity).
- Whitespace allowed between tokens: space, tab, `\n`, `\r`.
- Anything invalid (trailing commas, single quotes, unquoted keys, trailing garbage, unterminated input, bad escapes, ...) raises `ValueError`.
