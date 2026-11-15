"""Remove the superseded Tilda module menu; retain the shared course navigation."""
from html.parser import HTMLParser
from pathlib import Path
import re

class LegacyMenu(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.lines = [0]
        for match in re.finditer('\n', source): self.lines.append(match.end())
        self.depth = 0
        self.start = None
        self.spans = []
        self.ids = []
    def source_offset(self):
        line, column = self.getpos()
        return self.lines[line - 1] + column
    def handle_starttag(self, tag, attrs):
        if tag != 'div': return
        attrs = dict(attrs)
        if self.start is None and attrs.get('data-record-type') == '2433':
            self.start = self.source_offset()
            self.depth = 0
            self.ids.append(attrs['id'])
        if self.start is not None: self.depth += 1
    def handle_endtag(self, tag):
        if tag != 'div' or self.start is None: return
        self.depth -= 1
        if self.depth == 0:
            self.spans.append((self.start, self.source_offset() + len('</div>')))
            self.start = None

root = Path(__file__).resolve().parents[1] / 'dist'
for path in root.rglob('*.html'):
    source = path.read_text()
    if 'class="course-navigation"' not in source: continue
    parser = LegacyMenu(source)
    parser.feed(source)
    for start, end in reversed(parser.spans): source = source[:start] + source[end:]
    source = source.replace('<nav class="course-navigation"', '<nav id="course-navigation" class="course-navigation"')
    for old_id in parser.ids: source = source.replace('href="#' + old_id + '"', 'href="#course-navigation"')
    path.write_text(source)
    if parser.spans: print(path.relative_to(root), ': removed old dropdown menu')
