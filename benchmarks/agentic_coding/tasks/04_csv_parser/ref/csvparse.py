def parse_csv(text, delimiter=","):
    if not text:
        return []
    rows, row, field = [], [], []
    i, n = 0, len(text)
    in_q = after_q = False
    while i < n:
        c = text[i]
        if in_q:
            if c == '"':
                if i + 1 < n and text[i + 1] == '"':
                    field.append('"'); i += 2; continue
                in_q, after_q = False, True; i += 1; continue
            field.append(c); i += 1; continue
        if c == delimiter:
            row.append(''.join(field)); field = []; after_q = False; i += 1; continue
        if c == '\n' or (c == '\r' and i + 1 < n and text[i + 1] == '\n'):
            row.append(''.join(field)); rows.append(row); row, field = [], []; after_q = False
            i += 2 if c == '\r' else 1; continue
        if after_q:
            raise ValueError("unexpected character after closing quote at %d" % i)
        if c == '"' and not field:
            in_q = True; i += 1; continue
        field.append(c); i += 1
    if in_q:
        raise ValueError("unterminated quoted field")
    if not text.endswith('\n'):
        row.append(''.join(field)); rows.append(row)
    return rows


def to_csv(rows, delimiter=","):
    out = []
    for r in rows:
        cells = []
        for f in r:
            f = str(f)
            if any(ch in f for ch in (delimiter, '"', '\r', '\n')):
                f = '"' + f.replace('"', '""') + '"'
            cells.append(f)
        out.append(delimiter.join(cells) + "\r\n")
    return ''.join(out)
