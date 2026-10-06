import sys
from functools import lru_cache

sys.setrecursionlimit(max(sys.getrecursionlimit(), 20000))


def _compile(p):
    toks, i, n = [], 0, len(p)
    while i < n:
        c = p[i]
        if c in '*+?':
            if not toks or toks[-1][1] != '1':
                raise ValueError("nothing to repeat at %d" % i)
            toks[-1] = (toks[-1][0], c)
            i += 1
            continue
        if c == '\\':
            if i + 1 >= n:
                raise ValueError("trailing backslash")
            toks.append((('lit', p[i + 1]), '1')); i += 2; continue
        if c == '[':
            j, neg, items, first = i + 1, False, [], True
            if j < n and p[j] == '^':
                neg = True; j += 1
            while True:
                if j >= n:
                    raise ValueError("unterminated class")
                ch = p[j]
                if ch == ']' and not first:
                    break
                if ch == '\\':
                    if j + 1 >= n:
                        raise ValueError("unterminated class")
                    ch = p[j + 1]; j += 2
                else:
                    j += 1
                if j + 1 < n and p[j] == '-' and p[j + 1] != ']':
                    hi = p[j + 1]; j += 2
                    if hi == '\\':
                        if j >= n:
                            raise ValueError("unterminated class")
                        hi = p[j]; j += 1
                    if hi < ch:
                        raise ValueError("bad range")
                    items.append((ch, hi))
                else:
                    items.append((ch, ch))
                first = False
            toks.append((('cls', neg, tuple(items)), '1')); i = j + 1; continue
        if c == '.':
            toks.append((('any',), '1')); i += 1; continue
        toks.append((('lit', c), '1')); i += 1
    out = []
    for mt, q in toks:
        if q == '+':
            out.append((mt, '1')); out.append((mt, '*'))
        else:
            out.append((mt, q))
    return out


def _ok(mt, ch):
    if mt[0] == 'any': return True
    if mt[0] == 'lit': return mt[1] == ch
    hit = any(a <= ch <= b for a, b in mt[2])
    return hit != mt[1]


def _strip(p):
    a = p.startswith('^')
    if a: p = p[1:]
    z = False
    if p.endswith('$'):
        k = len(p) - 1; bs = 0
        while k - 1 - bs >= 0 and p[k - 1 - bs] == '\\': bs += 1
        if bs % 2 == 0:
            z = True; p = p[:-1]
    return p, a, z


def _matcher(toks, text, must_end):
    n, T = len(text), len(toks)

    @lru_cache(maxsize=None)
    def m(ti, si):
        if ti == T:
            return si == n if must_end else True
        mt, q = toks[ti]
        if q == '1':
            return si < n and _ok(mt, text[si]) and m(ti + 1, si + 1)
        if q == '?':
            return m(ti + 1, si) or (si < n and _ok(mt, text[si]) and m(ti + 1, si + 1))
        return m(ti + 1, si) or (si < n and _ok(mt, text[si]) and m(ti, si + 1))
    return m


def fullmatch(pattern, text):
    p, _, _ = _strip(pattern)
    return _matcher(tuple(_compile(p)), text, True)(0, 0)


def search(pattern, text):
    p, a, z = _strip(pattern)
    m = _matcher(tuple(_compile(p)), text, z)
    starts = [0] if a else range(len(text) + 1)
    return any(m(0, s) for s in starts)
