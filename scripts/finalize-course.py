"""Pre-render translations and isolate the original embedded exercises."""
from pathlib import Path
from html import escape, unescape
import json,re

DIST=Path(__file__).resolve().parents[1]/'dist'
for lang in ('tr','ru'):
    dictionary=json.loads((DIST/'assets'/f'course-{lang}.json').read_text())
    entries={k:v for k,v in dictionary.items() if k!=v}
    pattern=re.compile(r'(?<!\w)(?:'+'|'.join(re.escape(k) for k in sorted(entries,key=len,reverse=True))+r')(?!\w)')
    def translate(text):
        decoded=unescape(text)
        stripped=decoded.strip()
        if not stripped:return text
        if stripped in entries: translated=decoded.replace(stripped,entries[stripped])
        else:translated=pattern.sub(lambda m:entries[m.group(0)],decoded)
        return escape(translated,quote=False)
    for path in DIST.rglob('*.html'):
        if lang not in path.relative_to(DIST).parts:continue
        content=path.read_text()
        blocks=re.split(r'(<(?:script|style|svg|code|pre|nav|aside)\b[^>]*>[\s\S]*?</(?:script|style|svg|code|pre|nav|aside)>)',content,flags=re.I)
        for i in range(0,len(blocks),2):
            pieces=re.split(r'(<[^>]*>)',blocks[i])
            blocks[i]=''.join(piece if j%2 else translate(piece) for j,piece in enumerate(pieces))
        path.write_text(''.join(blocks))

# Separate embedded exercises share common variable/function names in the original.
# Isolate their scopes while retaining their local DOM event handlers.
for path in DIST.rglob('*.html'):
    content=path.read_text()
    def isolate(m):
        opening,body=m.group(1),m.group(2)
        if 'src=' in opening or 'application/' in opening:return m.group(0)
        if 'courseExerciseRoot' in body:return m.group(0)
        if ('getElementById' in body and 'addEventListener' in body) or re.search(r'\b(?:const|let)\s+(?:scenarios|questions|content|tasks|steps|cards|sources|cases|items|checklist|options|checks|dilemmas|quizData|flashcards)\b',body):
            scope='''
const courseExerciseRoot = globalThis.document.currentScript.closest('.t-rec') || globalThis.document;
const document = new Proxy(globalThis.document, { get(target, key) {
  if (key === 'querySelector' || key === 'querySelectorAll') return courseExerciseRoot[key].bind(courseExerciseRoot);
  if (key === 'getElementById') return id => courseExerciseRoot.querySelector('#' + CSS.escape(id));
  const value = Reflect.get(target, key, target);
  return typeof value === 'function' ? value.bind(target) : value;
}});
'''
            if body.lstrip().startswith('(() => {'):
                body=body.replace('(() => {','(() => {\n'+scope,1)
            else:body='\n(() => {\n'+scope+body+'\n})();\n'
            return opening+body+'</script>'
        return m.group(0)
    path.write_text(re.sub(r'(<script\b[^>]*>)([\s\S]*?)</script>',isolate,content))
print('Static translations rendered; exercise scopes isolated.')
