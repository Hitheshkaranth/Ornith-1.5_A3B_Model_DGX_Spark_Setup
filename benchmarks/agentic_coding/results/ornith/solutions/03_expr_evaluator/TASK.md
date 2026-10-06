Create `calc.py` with `evaluate(expr: str)` and exception class `CalcError` (a subclass of `ValueError`).

`evaluate` parses and computes an arithmetic expression and returns a number (int or float, compared with tolerance).
You MUST write your own tokenizer/parser: do not use `eval`, `exec`, `compile` or the `ast` module.

Grammar / semantics:
- Numbers: digits with at most one decimal point, at least one digit (`12`, `1.5`, `.5`, `5.` are valid; `1..2` and `.` are not).
- Binary operators: `+ - * / % **`. `/` is true division, `%` follows Python semantics.
- Precedence (high to low): `**` (right-associative), unary `+`/`-`, then `* / %` (left-assoc), then `+ -` (left-assoc).
  So `-2**2 == -4`, `2**3**2 == 512`, `2**-1 == 0.5`, `3*-2 == -6`, `--3 == 3`.
- Parentheses for grouping. Whitespace (spaces, tabs) is ignored.
- Raise `CalcError` for: empty input, unknown characters, malformed numbers, unbalanced parentheses, missing operands,
  two operands without an operator (`2 3`, `2(3)` — there is no implicit multiplication), and division or modulo by zero.
