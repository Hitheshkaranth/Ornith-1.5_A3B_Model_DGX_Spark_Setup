"""A small arithmetic expression evaluator.

Implements ``evaluate(expr)`` using a hand-written tokenizer and
recursive-descent parser. It does not use ``eval``/``exec``/``compile``
nor the ``ast`` module.

Grammar (precedence, high to low):
    expression : term (('+' | '-') term)*                 # left assoc
    term       : factor (('*' | '/' | '%') factor)*       # left assoc
    factor     : ('+' | '-') factor | power
    power      : primary ('**' factor)?                   # right assoc
    primary    : NUMBER | '(' expression ')'
"""

__all__ = ["evaluate", "CalcError"]


class CalcError(ValueError):
    """Raised when an expression cannot be parsed or evaluated."""


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

_TOKEN_TYPES = {
    "+": "PLUS",
    "-": "MINUS",
    "*": "STAR",
    "/": "SLASH",
    "%": "PERCENT",
    "**": "POW",
    "(": "LPAREN",
    ")": "RPAREN",
}


def _tokenize(text):
    tokens = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c in " \t\r\n":
            i += 1
            continue

        # Numbers: run of digits and dots, but must contain a digit and
        # at most one dot.
        if c.isdigit() or c == ".":
            start = i
            while i < n and (text[i].isdigit() or text[i] == "."):
                i += 1
            num = text[start:i]
            if num.count(".") > 1 or not any(ch.isdigit() for ch in num):
                raise CalcError(f"malformed number: {num!r}")
            tokens.append(("NUMBER", float(num) if "." in num else int(num)))
            continue

        # Two-character operator '**'.
        if c == "*":
            if i + 1 < n and text[i + 1] == "*":
                tokens.append(("POW", "**"))
                i += 2
                continue
            tokens.append(("STAR", "*"))
            i += 1
            continue

        if c in _TOKEN_TYPES:
            kind = _TOKEN_TYPES[c]
            tokens.append((kind, c))
            i += 1
            continue

        raise CalcError(f"unexpected character: {c!r}")

    return tokens


# ---------------------------------------------------------------------------
# Recursive-descent parser
# ---------------------------------------------------------------------------


class _Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # -- helpers -------------------------------------------------------------

    def _peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _next(self):
        tok = self._peek()
        self.pos += 1
        return tok

    def _expect(self, kind):
        tok = self._peek()
        if tok is None or tok[0] != kind:
            raise CalcError(f"expected {kind} but found {self._describe()!r}")
        return self._next()

    def _describe(self):
        tok = self._peek()
        if tok is None:
            return "end of expression"
        return f"token {tok[0]} ({tok[1]})"

    # -- grammar rules -------------------------------------------------------

    def parse(self):
        if not self.tokens:
            raise CalcError("empty expression")
        value = self._expression()
        if self.pos != len(self.tokens):
            raise CalcError(f"unexpected {self._describe()}")
        return value

    def _expression(self):
        value = self._term()
        while True:
            tok = self._peek()
            if tok is not None and tok[0] in ("PLUS", "MINUS"):
                op = self._next()[0]
                right = self._term()
                value = _apply(op, value, right)
            else:
                return value

    def _term(self):
        value = self._factor()
        while True:
            tok = self._peek()
            if tok is not None and tok[0] in ("STAR", "SLASH", "PERCENT"):
                op = self._next()[0]
                right = self._factor()
                value = _apply(op, value, right)
            else:
                return value

    def _factor(self):
        tok = self._peek()
        if tok is not None and tok[0] in ("PLUS", "MINUS"):
            op = self._next()[0]
            operand = self._factor()
            return -operand if op == "MINUS" else operand
        return self._power()

    def _power(self):
        base = self._primary()
        tok = self._peek()
        if tok is not None and tok[0] == "POW":
            self._next()
            # The exponent is a factor: this gives right-associativity for
            # chains like ``2**3**2`` and allows a unary sign like ``2**-1``.
            exponent = self._factor()
            return _apply("POW", base, exponent)
        return base

    def _primary(self):
        tok = self._peek()
        if tok is None:
            raise CalcError("missing operand")
        if tok[0] == "NUMBER":
            self._next()
            return tok[1]
        if tok[0] == "LPAREN":
            self._next()
            value = self._expression()
            self._expect("RPAREN")
            return value
        raise CalcError(f"unexpected {self._describe()}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_OP = {
    "PLUS": lambda a, b: a + b,
    "MINUS": lambda a, b: a - b,
    "STAR": lambda a, b: a * b,
    "SLASH": lambda a, b: a / b,
    "PERCENT": lambda a, b: a % b,
    "POW": lambda a, b: a ** b,
}


def _apply(op, a, b):
    if op in ("SLASH", "PERCENT") and b == 0:
        if op == "SLASH":
            raise CalcError("division by zero")
        raise CalcError("modulo by zero")
    try:
        return _OP[op](a, b)
    except ZeroDivisionError:
        raise CalcError("division by zero")


def evaluate(expr: str):
    """Parse and evaluate an arithmetic expression.

    Returns an ``int`` or ``float``. Raises :class:`CalcError` on any
    malformed input or mathematical error.
    """
    if expr is None or not isinstance(expr, str):
        raise CalcError("expression must be a string")
    if expr.strip() == "":
        raise CalcError("empty expression")
    tokens = _tokenize(expr)
    if not tokens:
        raise CalcError("empty expression")
    return _Parser(tokens).parse()