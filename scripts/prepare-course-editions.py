from pathlib import Path
import json,re
D=Path('dist')
manual={'tr':{'Misinformation':'Yanlış bilgi','Disinformation':'Dezenformasyon','Malinformation':'Kötücül bilgi','Show Score':'Puanı göster','AI only':'Yalnızca yapay zekâ','Human only':'Yalnızca insan','AI + Human':'Yapay zekâ + insan','AI+Human':'Yapay zekâ + insan','Human':'İnsan','AI':'Yapay zekâ','✅ Correct':'✅ Doğru','❌ Incorrect. Correct:':'❌ Yanlış. Doğru yanıt:','❌ Incorrect. Best tool:':'❌ Yanlış. En uygun araç:','Reverse image search':'Tersine görsel arama'},'ru':{'Misinformation':'Непреднамеренно ложная информация','Disinformation':'Преднамеренная дезинформация','Malinformation':'Достоверная информация во вред','Show Score':'Показать результат','AI only':'Только ИИ','Human only':'Только человек','AI + Human':'ИИ + человек','AI+Human':'ИИ + человек','Human':'Человек','AI':'ИИ','✅ Correct':'✅ Верно','❌ Incorrect. Correct:':'❌ Неверно. Правильный ответ:','❌ Incorrect. Best tool:':'❌ Неверно. Подходящий инструмент:','Reverse image search':'Обратный поиск изображений'}}
for lang,terms in manual.items():
 p=D/'assets'/f'course-{lang}.json';d=json.loads(p.read_text());d.update(terms);p.write_text(json.dumps(d,ensure_ascii=False))
labels={'en':('Home','Course modules'),'tr':('Ana sayfa','Ders modülleri'),'ru':('Главная','Модули курса')}
def clean(s):
 s=re.sub(r'<nav class="course-navigation"[\s\S]*?</nav>','',s)
 s=re.sub(r'<aside class="course-translation-note"[\s\S]*?</aside>','',s)
 s=re.sub(r'<script[^>]*src="[^"]*course-localize.js"[^>]*></script>','',s)
 return s
for lang in ['en','tr','ru']:
 for i in range(7):
  path=D/(f'module{i}/{lang}/index.html' if i else f'{lang}/index.html')
  if lang!='en' and (i or lang=='ru'):
   source=D/(f'module{i}/en/index.html' if i else 'en/index.html');s=clean(source.read_text());s=s.replace('/en/index.html','/'+lang+'/index.html')
  else:s=clean(path.read_text())
  s=re.sub(r'<html([^>]*) lang="[^"]*">',lambda m:'<html'+m.group(1)+f' lang="{lang}">',s,count=1)
  root='../../' if i else '../';route=f'module{i}/' if i else ''
  home,mods=labels[lang]
  nav=f'<nav class="course-navigation" aria-label="Course navigation"><a href="{root}index.html">{home}</a><span>{mods}:</span>'
  nav+=''.join(f'<a href="{root}module{n}/{lang}/index.html">{n}</a>' for n in range(1,7))
  nav+='<span class="course-languages">'+''.join(f'<a href="{root}{route}{code}/index.html" lang="{code}"'+(' aria-current="page"' if code==lang else '')+f'>{code.upper()}</a>' for code in ('en','tr','ru'))+'</span></nav>'
  if lang!='en':
   note={'tr':'Bu sürüm, İngilizce kaynak dersten otomatik olarak çevrilmiştir. Görseller, alıntılar ve ses kayıtları özgün dilinde kalabilir.','ru':'Эта версия автоматически переведена с английского курса. Изображения, цитаты и аудиозаписи могут оставаться на языке оригинала.'}[lang]
   nav+=f'<aside class="course-translation-note">{note}</aside>'
   s=s.replace('</head>',f'<script defer src="{root}assets/course-localize.js" data-locale="{lang}" data-dictionary="{root}assets/course-{lang}.json"></script></head>',1)
  s=re.sub(r'(<body\b[^>]*>)',lambda m:m.group(1)+nav,s,count=1)
  path.write_text(s)
