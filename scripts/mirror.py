"""Preserve the owner's Tilda pages and vendor their static dependencies."""
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urlsplit, urljoin, unquote
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import re
import posixpath
import subprocess
import gzip

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dist'
ORIGIN = 'https://kahramanhumeyrafinal.tilda.ws'
URLS = re.compile(r'https?://[^\s\"\'<>\\)]+')
pages = {'/verificationliteracy/homepage': 'index.html', '/': 'blog/index.html', '/en': 'en/index.html', '/tr': 'tr/index.html', '/ru': 'ru/index.html'}
assets = {}
failures = []

def fetch(url):
    if url == ORIGIN + '/verificationliteracy/homepage' and Path('/tmp/verification-original.html').exists():
        return Path('/tmp/verification-original.html').read_bytes()
    cache = ROOT / '.mirror-cache' / hashlib.sha256(url.encode()).hexdigest()
    if cache.exists():
        return cache.read_bytes()
    data = subprocess.run(['curl', '-L', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout
    if data.startswith(b'\x1f\x8b'):
        data = gzip.decompress(data)
    cache.parent.mkdir(exist_ok=True)
    cache.write_bytes(data)
    return data

def asset_path(url):
    ext = Path(unquote(urlsplit(url).path)).suffix
    if not re.fullmatch(r'\.[a-zA-Z0-9]{1,6}', ext):
        ext = '.bin'
    return 'assets/' + hashlib.sha256(url.encode()).hexdigest()[:20] + ext

def is_asset(url):
    return urlsplit(url).hostname and urlsplit(url).hostname.endswith(('tildacdn.net', 'tildacdn.com', 'tildacdn.info')) and bool(Path(urlsplit(url).path).suffix)

def relative(target, current):
    return posixpath.relpath(target, posixpath.dirname(current) or '.')

documents = {}
for path, local in list(pages.items()):
    print('Page:', path, flush=True)
    try:
        documents[local] = fetch(ORIGIN + path).decode('utf-8')
    except Exception as e:
        failures.append({'url': ORIGIN + path, 'error': str(e)})

# Discover additional same-site linked pages, with a firm limit.
for _ in range(3):
    discovered = set()
    for content in documents.values():
        for href in re.findall(r'href=[\"\']([^\"\']+)', content):
            full = urljoin(ORIGIN + '/', href)
            p = urlsplit(full)
            if p.path and p.netloc == urlsplit(ORIGIN).netloc and p.path not in pages and not Path(p.path).suffix and len(pages) + len(discovered) < 35:
                discovered.add(p.path)
    if not discovered:
        break
    for path in sorted(discovered):
        local = path.strip('/') + '/index.html'
        pages[path] = local
        try:
            print('Linked page:', path, flush=True)
            documents[local] = fetch(ORIGIN + path).decode('utf-8')
        except Exception as e:
            failures.append({'url': ORIGIN + path, 'error': str(e)})

pending = set(u for s in documents.values() for u in URLS.findall(s) if is_asset(u))
def download(url):
    try:
        return url, fetch(url), None
    except Exception as e:
        return url, None, str(e)

for _ in range(5):
    pending -= assets.keys()
    if not pending:
        break
    batch = sorted(pending)
    pending = set()
    print('Downloading', len(batch), 'assets', flush=True)
    with ThreadPoolExecutor(max_workers=10) as pool:
        for url, data, error in pool.map(download, batch):
            if error:
                failures.append({'url': url, 'error': error})
                assets[url] = None
                continue
            local = asset_path(url)
            assets[url] = {'path': local, 'data': data}
            if local.endswith('.css'):
                css = data.decode('utf-8')
                for ref in re.findall(r'url\([\"\']?([^\)\"\']+)', css):
                    full = urljoin(url, ref)
                    if not ref.startswith('data:'):
                        pending.add(full)

for url, entry in assets.items():
    if not entry:
        continue
    data = entry['data']
    if entry['path'].endswith('.css'):
        css = data.decode('utf-8')
        def replace_css(m):
            ref = m.group(1)
            item = assets.get(urljoin(url, ref))
            return 'url("' + relative(item['path'], entry['path']) + '")' if item else m.group(0)
        css = re.sub(r'url\([\"\']?([^\)\"\']+)[\"\']?\)', replace_css, css)
        data = css.encode()
    target = OUT / entry['path']
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)

for local, content in documents.items():
    for url in sorted(assets, key=len, reverse=True):
        if assets[url]:
            content = content.replace(url, relative(assets[url]['path'], local))
    def replace_link(m):
        href = m.group(2)
        p = urlsplit(urljoin(ORIGIN + '/', href))
        target = pages.get(p.path)
        if (href.startswith('/') or href.startswith(('https://', 'http://'))) and p.netloc == urlsplit(ORIGIN).netloc and target in documents:
            href = relative(target, local) + ('#' + p.fragment if p.fragment else '')
        elif href.startswith('/') and not href.startswith('//'):
            href = ORIGIN + href
        return m.group(1) + href + m.group(3)
    content = re.sub(r'(href=[\"\'])([^\"\']+)([\"\'])', replace_link, content)
    # Show full-resolution local backgrounds without waiting for Tilda's CDN lazy loader.
    def full_image(m):
        tag = m.group(0)
        original = re.search(r'data-original="([^"]+)"', tag)
        if original:
            tag = re.sub(r'url\([^)]*\)', "url('" + original.group(1) + "')", tag)
        return tag
    content = re.sub(r'<[^>]+data-original="[^>]+>', full_image, content)
    target = OUT / local
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)

# Retain the original homepage path for old bookmarks.
alias = OUT / 'verificationliteracy/homepage/index.html'
alias.parent.mkdir(parents=True, exist_ok=True)
home = documents.get('index.html', '')
if home:
    transformed = (OUT / 'index.html').read_text()
    transformed = transformed.replace('<head>', '<head><base href="../../">', 1)
    alias.write_text(transformed)
(OUT / '.nojekyll').touch()
report = {'pages': list(documents), 'assets': sum(bool(v) for v in assets.values()), 'failures': failures}
(ROOT / 'mirror-report.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2), flush=True)
