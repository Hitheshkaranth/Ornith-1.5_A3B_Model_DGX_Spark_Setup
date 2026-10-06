import re

_LINK = re.compile(r'\[([^\]]+)\]\(([^)\s]+)\)')
_BOLD = re.compile(r'\*\*(?!\s)(.+?)(?<!\s)\*\*')
_EM = re.compile(r'\*(?!\s)(.+?)(?<!\s)\*')
_OL = re.compile(r'^\d+\. ')
_H = re.compile(r'^(#{1,6}) (.*)$')


def _esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _emph(t):
    t = _BOLD.sub(r'<strong>\1</strong>', t)
    return _EM.sub(r'<em>\1</em>', t)


def _fmt(s):
    out, pos = [], 0
    for m in _LINK.finditer(s):
        out.append(_emph(_esc(s[pos:m.start()])))
        url = m.group(2).replace('&', '&amp;').replace('"', '&quot;')
        out.append('<a href="%s">%s</a>' % (url, _emph(_esc(m.group(1)))))
        pos = m.end()
    out.append(_emph(_esc(s[pos:])))
    return ''.join(out)


def _inline(s):
    out = []
    for p in re.split(r'(`[^`]*`)', s):
        if len(p) >= 2 and p[0] == '`' and p[-1] == '`':
            out.append('<code>' + _esc(p[1:-1]) + '</code>')
        else:
            out.append(_fmt(p))
    return ''.join(out)


def _kind(line):
    if line.startswith('```'): return 'fence'
    if _H.match(line): return 'h'
    if line.startswith('- ') or line.startswith('* '): return 'ul'
    if _OL.match(line): return 'ol'
    if not line.strip(): return 'blank'
    return 'p'


def render(text):
    lines = text.split('\n')
    blocks, i = [], 0
    while i < len(lines):
        line = lines[i]; k = _kind(line)
        if k == 'blank':
            i += 1
        elif k == 'fence':
            lang = line[3:].strip(); i += 1; body = []
            while i < len(lines) and lines[i].rstrip() != '```':
                body.append(_esc(lines[i])); i += 1
            i += 1
            cls = ' class="language-%s"' % lang if lang else ''
            blocks.append('<pre><code%s>%s</code></pre>' % (cls, '\n'.join(body)))
        elif k == 'h':
            m = _H.match(line); n = len(m.group(1))
            blocks.append('<h%d>%s</h%d>' % (n, _inline(m.group(2).strip()), n)); i += 1
        elif k in ('ul', 'ol'):
            items = []
            while i < len(lines) and _kind(lines[i]) == k:
                body = lines[i][2:] if k == 'ul' else _OL.sub('', lines[i], count=1)
                items.append('<li>%s</li>' % _inline(body.strip())); i += 1
            blocks.append('<%s>%s</%s>' % (k, ''.join(items), k))
        else:
            para = []
            while i < len(lines) and _kind(lines[i]) == 'p':
                para.append(lines[i].strip()); i += 1
            blocks.append('<p>%s</p>' % _inline(' '.join(para)))
    return '\n'.join(blocks)
