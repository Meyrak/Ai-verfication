"""Keep internal navigation in the current tab and link directly to the blog."""
from pathlib import Path
from urllib.parse import urlsplit
import re

root = Path(__file__).resolve().parents[1] / 'dist'
for path in root.rglob('*.html'):
    content = path.read_text()
    if path == root / 'index.html' or path == root / 'verificationliteracy/homepage/index.html':
        content = content.replace('href="#rec2302453023"', 'href="blog/index.html"')
    def same_tab(match):
        tag = match.group(0)
        href = re.search(r'\bhref=[\"\']([^\"\']*)', tag)
        if not href: return tag
        url = urlsplit(href.group(1))
        if (not url.scheme and not url.netloc) or url.netloc == 'meyrak.github.io':
            tag = re.sub(r'\s+target=[\"\'][^\"\']*[\"\']', '', tag)
        return tag
    updated = re.sub(r'<a\b[^>]*>', same_tab, content)
    if updated != path.read_text(): path.write_text(updated)
