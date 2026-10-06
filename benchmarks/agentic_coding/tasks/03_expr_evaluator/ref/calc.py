class CalcError(ValueError):
    pass


def _tokenize(s):
    toks, i = [], 0
    while i < len(s):
        c = s[i]
        if c.isspace():
            i += 1; continue
        if c.isdigit() or c == '.':
            j, dots = i, 0
            while j < len(s) and (s[j].isdigit() or s[j] == '.'):
                dots += s[j] == '.'; j += 1
            txt = s[i:j]
            if dots > 1 or txt == '.':
                raise CalcError("bad number %r" % txt)
            toks.append(('num', float(txt) if dots else int(txt))); i = j; continue
        if s.startswith('**', i):
            toks.append(('op', '**')); i += 2; continue
        if c in '+-*/%()':
            toks.append(('op', c)); i += 1; continue
        raise CalcError("unexpected %r" % c)
    return toks


class _P:
    def __init__(s, t): s.t, s.i = t, 0
    def peek(s): return s.t[s.i] if s.i < len(s.t) else (None, None)
    def take(s): tok = s.peek(); s.i += 1; return tok
    def isop(s, *ops): k, v = s.peek(); return k == 'op' and v in ops

    def expr(s):
        v = s.term()
        while s.isop('+', '-'):
            op = s.take()[1]; r = s.term(); v = v + r if op == '+' else v - r
        return v

    def term(s):
        v = s.unary()
        while s.isop('*', '/', '%'):
            op = s.take()[1]; r = s.unary()
            if op == '*':
                v = v * r
            else:
                if r == 0: raise CalcError("division by zero")
                v = v / r if op == '/' else v % r
        return v

    def unary(s):
        if s.isop('+', '-'):
            op = s.take()[1]; v = s.unary(); return -v if op == '-' else v
        return s.power()

    def power(s):
        b = s.atom()
        if s.isop('**'):
            s.take(); e = s.unary()
            try:
                return b ** e
            except ZeroDivisionError:
                raise CalcError("division by zero")
        return b

    def atom(s):
        k, v = s.take()
        if k == 'num': return v
        if (k, v) == ('op', '('):
            r = s.expr()
            if s.take() != ('op', ')'): raise CalcError("expected )")
            return r
        raise CalcError("unexpected token")


def evaluate(expr):
    p = _P(_tokenize(expr))
    if not p.t: raise CalcError("empty")
    v = p.expr()
    if p.i != len(p.t): raise CalcError("trailing input")
    return v
