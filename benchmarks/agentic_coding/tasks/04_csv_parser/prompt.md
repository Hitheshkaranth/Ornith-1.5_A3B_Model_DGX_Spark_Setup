Create `csvparse.py` with two functions. Do NOT use the `csv` module.

`parse_csv(text: str, delimiter: str = ",") -> list[list[str]]`
- Records are separated by `\n` or `\r\n`. A single trailing line break at the end of the input does not create an extra record. Empty input returns `[]`.
- Fields are separated by `delimiter`. A field may be enclosed in double quotes; inside quotes `""` is a literal `"`, and delimiters and line breaks are literal text.
- After a closing quote the next character must be the delimiter, a line break, or end of input; otherwise raise `ValueError`.
- A `"` appearing inside an unquoted field (not at its start) is a literal character (`ab"c` -> `ab"c`).
- An unterminated quoted field raises `ValueError`.
- An empty line produces the record `['']`.

`to_csv(rows, delimiter=",") -> str`
- Quote a field (doubling inner quotes) iff it contains the delimiter, `"`, `\r` or `\n`.
- Each row is terminated by `\r\n` (including the last one).
- `parse_csv(to_csv(rows)) == rows` must hold for any list of rows of strings (each row with at least one field).
