"""Remove platform promotion, tracking loaders, and obsolete public metadata."""
from html.parser import HTMLParser
from pathlib import Path
import hashlib,re

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'
PUBLIC='https://meyrak.github.io/Ai-verfication/'

class Branding(HTMLParser):
    def __init__(self,source):
        super().__init__();self.lines=[0];self.start=None;self.depth=0;self.spans=[]
        for m in re.finditer('\n',source):self.lines.append(m.end())
    def source_offset(self):
        row,col=self.getpos();return self.lines[row-1]+col
    def handle_starttag(self,tag,attrs):
        if tag!='div':return
        attrs=dict(attrs)
        if self.start is None and (attrs.get('id')=='tildacopy' or 't-tildalabel' in attrs.get('class','').split()):
            self.start=self.source_offset();self.depth=0
        if self.start is not None:self.depth+=1
    def handle_endtag(self,tag):
        if tag!='div' or self.start is None:return
        self.depth-=1
        if not self.depth:self.spans.append((self.start,self.source_offset()+6));self.start=None

def asset(url):return hashlib.sha256(url.encode()).hexdigest()[:20]+'.js'
unneeded={asset('https://neo.tildacdn.com/js/tilda-fallback-1.0.min.js'),asset('https://static.tildacdn.net/js/tilda-events-1.0.min.js')}
for path in DIST.rglob('*.html'):
    s=path.read_text();parser=Branding(s);parser.feed(s)
    for start,end in reversed(parser.spans):s=s[:start]+s[end:]
    s=re.sub(r'<!--[^>]*[Tt]ilda[^>]*-->','',s)
    def script(m):
        opening,body=m.group(1),m.group(2)
        if 'tildastatscript' in body or 'window.mainTracker' in body:return ''
        if any(name in opening for name in unneeded):return ''
        return m.group(0)
    s=re.sub(r'(<script\b[^>]*>)([\s\S]*?)</script>',script,s)
    s=re.sub(r'<link\b(?=[^>]*rel=[\"\']dns-prefetch[\"\'])(?=[^>]*tilda)[^>]*>','',s)
    rel=path.relative_to(DIST);prefix='../'*(len(rel.parts)-1)
    if 'verificationliteracy' in rel.parts:prefix='' # This alias already has a homepage base URL.
    s=re.sub(r'<link\b(?=[^>]*rel=[\"\'](?:shortcut )?icon[\"\'])[^>]*>',f'<link rel="icon" type="image/svg+xml" href="{prefix}assets/course-icon.svg">',s)
    route='' if str(rel)=='index.html' or 'verificationliteracy' in rel.parts else str(rel.parent)+'/'
    canonical=PUBLIC+route
    s=re.sub(r'<link\b(?=[^>]*rel=[\"\']canonical[\"\'])[^>]*>',f'<link rel="canonical" href="{canonical}">',s)
    s=re.sub(r'<meta\b(?=[^>]*property=[\"\']og:url[\"\'])[^>]*>',f'<meta property="og:url" content="{canonical}">',s)
    s=re.sub(r'<meta\b(?=[^>]*(?:name|content)=[\"\'][^\"\']*[Tt]ilda)[^>]*>','',s)
    s=re.sub(r'\sdata-tilda-(?:project-id|page-id|page-alias|formskey|project-country|root-zone|sign)=[\"\'][^\"\']*[\"\']','',s)
    s=s.replace('http://kahramanhumeyrafinal.tilda.ws',PUBLIC.rstrip('/'))
    path.write_text(s)
    print(rel, 'branding and tracker removed')
