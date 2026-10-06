import re

_NUM = re.compile(r'-?(?:0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?')
_ESC = {'"': '"', '\\': '\\', '/': '/', 'b': '\b', 'f': '\f', 'n': '\n', 'r': '\r', 't': '\t'}
_HEX = set('0123456789abcdefABCDEF')


class _P:
    def __init__(s, t): s.t, s.i = t, 0
    def err(s, m): raise ValueError("%s at %d" % (m, s.i))

    def ws(s):
        while s.i < len(s.t) and s.t[s.i] in ' \t\n\r': s.i += 1

    def value(s):
        s.ws()
        if s.i >= len(s.t): s.err("unexpected end")
        c = s.t[s.i]
        if c == '{': return s.obj()
        if c == '[': return s.arr()
        if c == '"': return s.string()
        if c == '-' or c in '0123456789': return s.num()
        for lit, val in (('true', True), ('false', False), ('null', None)):
            if s.t.startswith(lit, s.i):
                s.i += len(lit); return val
        s.err("unexpected character")

    def num(s):
        m = _NUM.match(s.t, s.i)
        if not m: s.err("bad number")
        s.i = m.end(); txt = m.group(0)
        return float(txt) if (m.group(1) or m.group(2)) else int(txt)

    def obj(s):
        s.i += 1; d = {}; s.ws()
        if s.i < len(s.t) and s.t[s.i] == '}':
            s.i += 1; return d
        while True:
            s.ws()
            if s.i >= len(s.t) or s.t[s.i] != '"': s.err("expected key")
            k = s.string(); s.ws()
            if s.i >= len(s.t) or s.t[s.i] != ':': s.err("expected :")
            s.i += 1; d[k] = s.value(); s.ws()
            if s.i < len(s.t) and s.t[s.i] == ',':
                s.i += 1; continue
            if s.i < len(s.t) and s.t[s.i] == '}':
                s.i += 1; return d
            s.err("expected , or }")

    def arr(s):
        s.i += 1; a = []; s.ws()
        if s.i < len(s.t) and s.t[s.i] == ']':
            s.i += 1; return a
        while True:
            a.append(s.value()); s.ws()
            if s.i < len(s.t) and s.t[s.i] == ',':
                s.i += 1; continue
            if s.i < len(s.t) and s.t[s.i] == ']':
                s.i += 1; return a
            s.err("expected , or ]")

    def hex4(s):
        h = s.t[s.i + 1:s.i + 5]
        if len(h) != 4 or any(ch not in _HEX for ch in h): s.err("bad \\u escape")
        s.i += 5; return int(h, 16)

    def string(s):
        s.i += 1; out = []
        while True:
            if s.i >= len(s.t): s.err("unterminated string")
            c = s.t[s.i]
            if c == '"':
                s.i += 1; return ''.join(out)
            if c == '\\':
                s.i += 1
                if s.i >= len(s.t): s.err("unterminated escape")
                e = s.t[s.i]
                if e in _ESC:
                    out.append(_ESC[e]); s.i += 1
                elif e == 'u':
                    cp = s.hex4()
                    if 0xD800 <= cp <= 0xDBFF and s.t.startswith('\\u', s.i):
                        save = s.i; s.i += 1; lo = s.hex4()
                        if 0xDC00 <= lo <= 0xDFFF:
                            cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00)
                        else:
                            s.i = save
                    out.append(chr(cp))
                else:
                    s.err("bad escape")
            elif ord(c) < 0x20:
                s.err("control character in string")
            else:
                out.append(c); s.i += 1


def loads(s):
    p = _P(s)
    v = p.value(); p.ws()
    if p.i != len(s): p.err("trailing data")
    return v
