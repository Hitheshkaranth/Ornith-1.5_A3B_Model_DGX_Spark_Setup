"""A small CSV parser/writer (standard library only; never imports `csv`)."""


def parse_csv(text, delimiter=","):
    """Parse CSV ``text`` into a list of records (each a list of fields).

    Records are separated by ``\\n`` or ``\\r\\n``. A single trailing line break
    does not create an extra record. Empty input yields ``[]``.
    """
    rows = []

    if text == "":
        return rows

    n = len(text)
    i = 0

    record = []          # current record (list of finished fields)
    field_chars = []     # buffer for the in-progress field
    in_quotes = False
    field_start = True
    last_was_linebreak = False

    def commit_field():
        record.append("".join(field_chars))
        field_chars.clear()

    def commit_record():
        commit_field()
        rows.append(list(record))
        record.clear()

    while i < n:
        c = text[i]
        last_was_linebreak = False

        if in_quotes:
            if c == '"':
                if i + 1 < n and text[i + 1] == '"':
                    field_chars.append('"')
                    i += 2
                    continue
                # Closing quote: next char must be delimiter/line break/EOF.
                in_quotes = False
                field_start = True
                i += 1
                if i < n and text[i] not in (delimiter, "\n", "\r"):
                    raise ValueError(
                        "character after closing quote must be a delimiter, "
                        "line break, or end of input"
                    )
                continue
            field_chars.append(c)
            i += 1
            continue

        # Not inside quotes.
        if field_start and c == '"':
            in_quotes = True
            field_start = False
            i += 1
            continue

        if c == delimiter:
            commit_field()
            field_start = True
            i += 1
            continue

        if c == "\r":
            if i + 1 < n and text[i + 1] == "\n":
                commit_record()
                i += 2
            else:
                commit_record()
                i += 1
            field_start = True
            last_was_linebreak = True
            continue

        if c == "\n":
            commit_record()
            field_start = True
            last_was_linebreak = True
            i += 1
            continue

        field_chars.append(c)
        field_start = False
        i += 1

    if in_quotes:
        raise ValueError("unterminated quoted field")

    if last_was_linebreak:
        # Input ended exactly at a line break; no trailing empty record.
        return rows

    commit_record()
    return rows


def to_csv(rows, delimiter=","):
    """Serialise ``rows`` (list of record lists) to CSV text.

    Fields are quoted (with inner quotes doubled) iff they contain the
    delimiter, a double quote, ``\\r`` or ``\\n``. Rows are terminated by
    ``\\r\\n`` (including the last one).
    """
    if not rows:
        return ""

    out_lines = []
    for row in rows:
        fields = []
        for field in row:
            if delimiter in field or '"' in field or "\r" in field or "\n" in field:
                fields.append('"' + field.replace('"', '""') + '"')
            else:
                fields.append(field)
        out_lines.append(delimiter.join(fields))

    return "\r\n".join(out_lines) + "\r\n"