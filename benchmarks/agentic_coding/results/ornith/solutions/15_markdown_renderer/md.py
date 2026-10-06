import re

_UL_RE = re.compile(r'[-*] ')
_OL_RE = re.compile(r'\d+\. ')
_HEADING_RE = re.compile(r'(#{1,6}) (.*)')


def _escape_plain(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _escape_url(s):
    return s.replace('&', '&amp;').replace('"', '&quot;')


def _is_ul(line):
    return _UL_RE.match(line) is not None


def _is_ol(line):
    return _OL_RE.match(line) is not None


def _is_paragraph_break(line):
    if line.startswith('```'):
        return True
    if _HEADING_RE.match(line):
        return True
    return _is_ul(line) or _is_ol(line)


def _is_emphasis(content):
    return bool(content) and content == content.strip()


def _inline(text):
    out = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == '`':
            k = 0
            while i < n and text[i] == '`':
                k += 1
                i += 1
            close = text.find('`' * k, i)
            if close != -1:
                out.append('<code>' + _escape_plain(text[i:close]) + '</code>')
                i = close + k
            else:
                out.append('`' * k)
            continue
        if ch == '[':
            r = text.find(']', i + 1)
            if r != -1 and r + 1 < n and text[r + 1] == '(':
                cp = text.find(')', r + 2)
                if cp != -1:
                    out.append('<a href="' + _escape_url(text[r + 2:cp]) + '">')
                    out.append(_inline(text[i + 1:r]))
                    out.append('</a>')
                    i = cp + 1
                    continue
            out.append(ch)
            i += 1
            continue
        if ch == '*':
            if text[i:i + 2] == '**':
                close = text.find('**', i + 2)
                if close != -1 and _is_emphasis(text[i + 2:close]):
                    out.append('<strong>')
                    out.append(_inline(text[i + 2:close]))
                    out.append('</strong>')
                    i = close + 2
                    continue
            close = text.find('*', i + 1)
            if close != -1 and _is_emphasis(text[i + 1:close]):
                out.append('<em>')
                out.append(_inline(text[i + 1:close]))
                out.append('</em>')
                i = close + 1
                continue
            out.append('*')
            i += 1
            continue
        j = i
        while j < n and text[j] not in '`[*':
            j += 1
        out.append(_escape_plain(text[i:j]))
        i = j
    return ''.join(out)


def render(text):
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    blocks = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.strip() == '':
            i += 1
            continue
        if line.startswith('```'):
            rest = line[3:].strip()
            lang = rest.split()[0] if rest else ''
            i += 1
            content = []
            while i < n and lines[i].strip() != '```':
                content.append(lines[i])
                i += 1
            if i < n:
                i += 1
            code_body = _escape_plain('\n'.join(content))
            if lang:
                blocks.append(
                    '<pre><code class="language-%s">%s</code></pre>' % (lang, code_body))
            else:
                blocks.append('<pre><code>%s</code></pre>' % code_body)
            continue
        m = _HEADING_RE.match(line)
        if m:
            lvl = len(m.group(1))
            blocks.append('<h%d>%s</h%d>' % (lvl, _inline(m.group(2).strip()), lvl))
            i += 1
            continue
        if _is_ul(line) or _is_ol(line):
            list_type = 'ul' if _is_ul(line) else 'ol'
            items = []
            while i < n and ((_is_ol(lines[i]) and list_type == 'ol')
                             or (_is_ul(lines[i]) and list_type == 'ul')):
                line_item = lines[i]
                if list_type == 'ul':
                    content = line_item[2:]
                else:
                    content = line_item[_OL_RE.match(line_item).end():]
                items.append('<li>' + _inline(content) + '</li>')
                i += 1
            blocks.append('<%s>%s</%s>' % (list_type, ''.join(items), list_type))
            continue
        para = []
        while i < n and lines[i].strip() != '' and not _is_paragraph_break(lines[i]):
            para.append(lines[i].strip())
            i += 1
        blocks.append('<p>%s</p>' % _inline(' '.join(para)))
    return '\n'.join(blocks)