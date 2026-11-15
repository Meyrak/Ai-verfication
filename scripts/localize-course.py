"""Generate local translations; translated text never changes quiz answer data."""
from pathlib import Path
from html.parser import HTMLParser
from html import unescape, escape
from concurrent.futures import ThreadPoolExecutor
import json, re, subprocess, hashlib, time
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
CACHE = ROOT / '.mirror-cache' / 'translations'
CACHE.mkdir(parents=True, exist_ok=True)

class Texts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.values = []
    def handle_starttag(self, tag, attrs):
        if tag in ('style', 'script', 'svg'): self.skip += 1
        for key, value in attrs:
            if key in ('alt', 'title', 'placeholder', 'aria-label') and value: self.values.append(value)
    def handle_endtag(self, tag):
        if tag in ('style', 'script', 'svg'): self.skip = max(0, self.skip - 1)
    def handle_data(self, data):
        if not self.skip and data.strip(): self.values.append(data.strip())

sources = [DIST / 'en/index.html', DIST / 'tr/index.html'] + [DIST / f'module{i}/en/index.html' for i in range(1,7)]
strings = set()
scripts = []
for path in sources:
    content = path.read_text()
    p = Texts(); p.feed(content)
    strings.update(p.values)
    for opening, body in re.findall(r'(<script\b[^>]*>)([\s\S]*?)</script>', content):
        if not re.search(r'\bsrc=', opening) and body.strip() and not re.search(r'application/(?:ld\+)?json', opening):
            scripts.append(body)
result = subprocess.run(['node', str(ROOT / 'scripts/extract-course-text.cjs')], input=json.dumps(scripts), text=True, capture_output=True, check=True)
parsed = json.loads(result.stdout)
errors = [r['error'] for r in parsed if r.get('error')]
if errors: raise RuntimeError('Inline JavaScript parse errors: ' + repr(errors))
for script in parsed:
    for value in script['strings']:
        if '<' in value and '>' in value:
            p = Texts(); p.feed(value); strings.update(p.values)
        elif '\n' not in value and len(value) < 2200:
            strings.add(value.strip())

def human(s):
    if not re.search('[A-Za-z]', s) or len(s) < 3: return False
    if re.match(r'^(https?:|mailto:|data:|#[\w-]+|\.[\w-]+|var\(|rgba?\()', s): return False
    if re.search(r'[{};]|document\.|querySelector|=>|\$\{|</', s): return False
    if not ' ' in s and re.search(r'[-_./:#]|[a-z][A-Z]',s): return False
    return True
strings = sorted(s for s in strings if human(s))
print('Extracted', len(strings), 'text strings from', len(scripts), 'scripts', flush=True)

def translate_batch(args):
    lang, items = args
    query = '\n'.join(f'ZXQ{i:06d}ZXQ {text}' for i, text in items)
    cache = CACHE / (lang + '-' + hashlib.sha256(query.encode()).hexdigest() + '.json')
    if cache.exists(): return json.loads(cache.read_text())
    url = 'https://translate.googleapis.com/translate_a/single?' + urlencode({'client':'gtx', 'sl':'auto', 'tl':lang, 'dt':'t', 'q':query})
    for attempt in range(4):
        try:
            data = subprocess.run(['curl','--fail','--silent','--show-error','--max-time','45',url], capture_output=True, check=True)
            response = json.loads(data.stdout)
            translated = ''.join(row[0] or '' for row in response[0])
            parts = re.split(r'ZXQ\s*(\d{6})\s*ZXQ', translated)
            found = {int(parts[i]):parts[i+1].strip() for i in range(1,len(parts)-1,2)}
            if any(i not in found for i,_ in items):
                if len(items)>1:
                    middle=len(items)//2
                    output={**translate_batch((lang,items[:middle])),**translate_batch((lang,items[middle:]))}
                    cache.write_text(json.dumps(output,ensure_ascii=False))
                    return output
                direct='https://translate.googleapis.com/translate_a/single?'+urlencode({'client':'gtx','sl':'auto','tl':lang,'dt':'t','q':items[0][1]})
                raw=subprocess.run(['curl','--fail','--silent','--show-error','--max-time','45',direct],capture_output=True,check=True)
                found[items[0][0]]=''.join(row[0] or '' for row in json.loads(raw.stdout)[0])
            output = {text:found[i] for i,text in items}
            cache.write_text(json.dumps(output,ensure_ascii=False))
            return output
        except Exception:
            if attempt == 3: raise
            time.sleep(1 + attempt)

batches=[]; batch=[]; size=0
for i, text in enumerate(strings):
    if size + len(text) > 2800 and batch:
        batches.append(batch);batch=[];size=0
    batch.append((i,text));size += len(text)+20
if batch:batches.append(batch)
for lang in ('tr','ru'):
    dictionary = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        for idx, translated in enumerate(pool.map(translate_batch, [(lang,b) for b in batches])):
            dictionary.update(translated)
            print(lang, 'batch',idx+1,'/',len(batches),flush=True)
    dictionary.update({'EN':lang.upper(), 'AI-Assisted Verification Coursebook': 'Yapay Zekâ Destekli Doğrulama Ders Kitabı' if lang=='tr' else 'Курс по проверке информации с помощью ИИ'})
    (DIST / 'assets' / f'course-{lang}.json').write_text(json.dumps(dictionary, ensure_ascii=False))

for lang in ('tr','ru'):
    source = DIST / 'en/index.html'
    # Keep the existing Turkish landing page and its original embedded activities.
    if lang=='ru':
        target=DIST / 'ru/index.html';target.parent.mkdir(exist_ok=True)
        target.write_text(source.read_text())
    for i in range(1,7):
        target=DIST / f'module{i}/{lang}/index.html';target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text((DIST / f'module{i}/en/index.html').read_text())

# Fix every same-site course link, then add shared navigation and translations.
nav_labels = {'en':('Home','Course modules','Translated course editions'), 'tr':('Ana sayfa','Ders modülleri','Çevrilmiş ders sürümleri'), 'ru':('Главная','Модули курса','Переводные версии курса')}
for path in DIST.rglob('*.html'):
    if 'verificationliteracy' in str(path): continue
    content=path.read_text()
    rel=path.relative_to(DIST)
    lang=next((v for v in ('en','tr','ru') if v in rel.parts),None)
    depth=len(rel.parts)-1;root='../'*depth
    def local_link(m):
        href=unescape(m.group(2))
        match=re.match(r'https?://kahramanhumeyrafinal\.tilda\.ws(/[^?#]*)?(.*)$',href)
        if match:
            route=(match.group(1) or '/').strip('/')
            target='blog/index.html' if not route else ('index.html' if route=='verificationliteracy/homepage' else route+'/index.html')
            if (DIST/target).exists(): return m.group(1)+root+target+match.group(2)+m.group(3)
        if lang and lang!='en' and re.search(r'module[1-6]/en/index.html',href):
            href=href.replace('/en/index.html','/'+lang+'/index.html')
            return m.group(1)+href+m.group(3)
        return m.group(0)
    content=re.sub(r'(href=[\"\'])([^\"\']+)([\"\'])',local_link,content)
    if lang:
        module=re.search(r'module([1-6])',str(rel))
        labels=nav_labels[lang]
        locale_path=(f'module{module.group(1)}/' if module else '')
        links=''.join(f'<a href="{root}{locale_path}{code}/index.html" lang="{code}"'+(' aria-current="page"' if code==lang else '')+f'>{code.upper()}</a>' for code in ('en','tr','ru'))
        modules=''.join(f'<a href="{root}module{i}/{lang}/index.html">{i}</a>' for i in range(1,7))
        notice={'tr':'İngilizce kaynak dersten çevrilmiştir. Kaynak alıntıları, görseller ve ses kayıtları özgün dilinde kalabilir.', 'ru':'Переведено с английской версии курса. Цитаты, изображения и аудиозаписи могут оставаться на языке оригинала.'}
        banner=f'<nav class="course-navigation" aria-label="Course navigation"><a href="{root}index.html">{labels[0]}</a><span>{labels[1]}:</span>{modules}<span class="course-languages">{links}</span></nav>'
        if lang!='en':banner+=f'<aside class="course-translation-note">{notice[lang]}</aside>'
        content=re.sub(r'<html\b([^>]*)>',lambda m:'<html'+re.sub(r'\s+lang=[\"\'][^\"\']*[\"\']','',m.group(1))+f' lang="{lang}">',content,count=1)
        content=content.replace('</head>',f'<link rel="stylesheet" href="{root}assets/course-navigation.css">'+(f'<script defer src="{root}assets/course-localize.js" data-locale="{lang}" data-dictionary="{root}assets/course-{lang}.json"></script>' if lang!='en' else '')+'</head>',1)
        content=re.sub(r'(<body\b[^>]*>)',lambda m:m.group(1)+banner,content,count=1)
    path.write_text(content)
alias=DIST/'verificationliteracy/homepage/index.html'
alias.write_text((DIST/'index.html').read_text().replace('<head>','<head><base href="../../">',1))
print('Created all three language editions and 18 modules.',flush=True)
