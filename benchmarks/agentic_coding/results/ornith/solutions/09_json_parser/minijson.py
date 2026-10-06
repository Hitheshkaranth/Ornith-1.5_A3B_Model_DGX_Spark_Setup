"""A strict JSON (RFC 8259) parser implemented without the standard library.

``loads`` parses a JSON document and returns the equivalent Python value,
matching ``json.loads`` (dict, list, str, int, float, True, False, None).
Anything that is not valid JSON raises ``ValueError``.
"""

_HEXDIGITS = frozenset("0123456789abcdefABCDEF")

_SIMPLE_ESCAPES = {
    '"': '"',
    "\\": "\\",
    "/": "/",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
}


class _Parser:
    """Recursive-descent parser over an immutable input string."""

    def __init__(self, text):
        self.s = text
        self.n = len(text)
        self.i = 0

    # -- top level -------------------------------------------------------
    def parse(self):
        self._skip_ws()
        if self.i >= self.n:
            raise ValueError("Empty JSON document")
        value = self._parse_value()
        self._skip_ws()
        if self.i != self.n:
            raise ValueError("Trailing characters after JSON value")
        return value

    def _skip_ws(self):
        s = self.s
        n = self.n
        i = self.i
        while i < n and s[i] in " \t\n\r":
            i += 1
        self.i = i

    # -- value dispatch --------------------------------------------------
    def _parse_value(self):
        if self.i >= self.n:
            raise ValueError("Unexpected end of input")
        c = self.s[self.i]
        if c == "{":
            return self._parse_object()
        if c == "[":
            return self._parse_array()
        if c == '"':
            return self._parse_string()
        if c == "-" or c.isdigit():
            return self._parse_number()
        if c == "t":
            return self._parse_literal("true", True)
        if c == "f":
            return self._parse_literal("false", False)
        if c == "n":
            return self._parse_literal("null", None)
        raise ValueError("Unexpected character %r" % (c,))

    def _parse_literal(self, word, value):
        end = self.i + len(word)
        if self.s[self.i:end] == word:
            self.i = end
            return value
        raise ValueError("Invalid literal")

    # -- object ----------------------------------------------------------
    def _parse_object(self):
        self.i += 1  # consume '{'
        obj = {}
        self._skip_ws()
        if self.i < self.n and self.s[self.i] == "}":
            self.i += 1
            return obj
        while True:
            self._skip_ws()
            if self.i >= self.n or self.s[self.i] != '"':
                raise ValueError("Expected string key in object")
            key = self._parse_string()
            self._skip_ws()
            if self.i >= self.n or self.s[self.i] != ":":
                raise ValueError("Expected ':' after object key")
            self.i += 1
            self._skip_ws()
            obj[key] = self._parse_value()
            self._skip_ws()
            if self.i >= self.n:
                raise ValueError("Unterminated object")
            c = self.s[self.i]
            if c == ",":
                self.i += 1
            elif c == "}":
                self.i += 1
                break
            else:
                raise ValueError("Expected ',' or '}' in object")
        return obj

    # -- array -----------------------------------------------------------
    def _parse_array(self):
        self.i += 1  # consume '['
        arr = []
        self._skip_ws()
        if self.i < self.n and self.s[self.i] == "]":
            self.i += 1
            return arr
        while True:
            self._skip_ws()
            arr.append(self._parse_value())
            self._skip_ws()
            if self.i >= self.n:
                raise ValueError("Unterminated array")
            c = self.s[self.i]
            if c == ",":
                self.i += 1
            elif c == "]":
                self.i += 1
                break
            else:
                raise ValueError("Expected ',' or ']' in array")
        return arr

    # -- string ----------------------------------------------------------
    def _parse_string(self):
        self.i += 1  # consume opening quote
        s = self.s
        n = self.n
        chars = []
        append = chars.append
        while True:
            if self.i >= n:
                raise ValueError("Unterminated string")
            c = s[self.i]
            if c == '"':
                self.i += 1
                return "".join(chars)
            if c == "\\":
                append(self._handle_escape())
            elif ord(c) < 0x20:
                raise ValueError("Raw control character in string")
            else:
                append(c)
                self.i += 1

    def _handle_escape(self):
        self.i += 1  # consume backslash
        if self.i >= self.n:
            raise ValueError("Unterminated escape sequence")
        esc = self.s[self.i]
        if esc in _SIMPLE_ESCAPES:
            self.i += 1
            return _SIMPLE_ESCAPES[esc]
        if esc == "u":
            return self._parse_unicode()
        raise ValueError("Invalid escape character %r" % (esc,))

    def _read_hex4(self):
        # self.i points at 'u'; consume it and the following 4 hex digits.
        if self.i + 5 > self.n:
            raise ValueError("Incomplete \\u escape sequence")
        hex_str = self.s[self.i + 1:self.i + 5]
        for ch in hex_str:
            if ch not in _HEXDIGITS:
                raise ValueError("Invalid \\u escape sequence")
        self.i += 5
        return int(hex_str, 16)

    def _parse_unicode(self):
        code = self._read_hex4()
        if 0xD800 <= code <= 0xDBFF:
            # High surrogate: look for a following low surrogate.
            if (self.i + 1 < self.n and self.s[self.i] == "\\"
                    and self.s[self.i + 1] == "u"):
                marker = self.i
                self.i += 1  # step onto the second 'u'
                code2 = self._read_hex4()
                if 0xDC00 <= code2 <= 0xDFFF:
                    combined = (
                        0x10000 + (code - 0xD800) * 0x400 + (code2 - 0xDC00)
                    )
                    return chr(combined)
                self.i = marker  # not a low surrogate; rescan it normally
            return chr(code)
        return chr(code)

    # -- number ----------------------------------------------------------
    def _parse_number(self):
        s = self.s
        n = self.n
        start = self.i
        i = self.i

        if s[i] == "-":
            i += 1
        if i >= n or s[i] == "0":
            i += 1
        elif "1" <= s[i] <= "9":
            i += 1
            while i < n and s[i].isdigit():
                i += 1
        else:
            raise ValueError("Invalid number")

        is_float = False
        if i < n and s[i] == ".":
            is_float = True
            i += 1
            if i >= n or not s[i].isdigit():
                raise ValueError("Invalid number fraction")
            while i < n and s[i].isdigit():
                i += 1

        if i < n and s[i] in "eE":
            is_float = True
            i += 1
            if i < n and s[i] in "+-":
                i += 1
            if i >= n or not s[i].isdigit():
                raise ValueError("Invalid number exponent")
            while i < n and s[i].isdigit():
                i += 1

        self.i = i
        text = s[start:i]
        if is_float:
            return float(text)
        return int(text)


def loads(s):
    """Parse a JSON document and return the corresponding Python value."""
    if not isinstance(s, str):
        raise ValueError("input must be a str")
    return _Parser(s).parse()