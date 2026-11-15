const fs=require('fs');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const target=await (await fetch('http://127.0.0.1:9223/json/new?about:blank',{method:'PUT'})).json();
 const ws=new WebSocket(target.webSocketDebuggerUrl);await new Promise(r=>ws.onopen=r);
 let id=0;const pending=new Map();let exceptions=[];
 ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id){const p=pending.get(m.id);if(p){pending.delete(m.id);m.error?p.reject(m.error):p.resolve(m.result);}}else if(m.method==='Runtime.exceptionThrown')exceptions.push(m.params.exceptionDetails.exception?.description||m.params.exceptionDetails.text);};
 const send=(method,params={})=>new Promise((resolve,reject)=>{const n=++id;pending.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method,params}));});
 const evaluate=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.text);return r.result.value;};
 await send('Runtime.enable');await send('Page.enable');
 const reports=[];
 for(const lang of ['en','tr','ru'])for(const module of [0,1,2,3,4,5,6]){
  exceptions=[];const route=module?`module${module}/${lang}/`:`${lang}/`;
  await send('Page.navigate',{url:(process.env.COURSE_BASE || 'http://127.0.0.1:8000/')+route});
  let ready=false;
  for(let n=0;n<150;n++){await sleep(100);ready=await evaluate(`document.readyState==='complete' && ${lang==='en'?'true':`document.documentElement.dataset.courseTranslated==='${lang}'`}`);if(ready)break;}
  const before=await evaluate(`({title:document.title,heading:document.querySelector('h1')?.innerText||'',buttons:document.querySelectorAll('button').length,language:document.documentElement.lang,links:[...document.querySelectorAll('a[href]')].map(a=>a.href).filter(h=>h.includes('kahramanhumeyrafinal.tilda.ws'))})`);
  const interacted=module?await evaluate(`(()=>{let count=0; for(const button of document.querySelectorAll('button')){if(button.closest('.course-navigation')||/copy|download/i.test(button.id+' '+button.className+' '+button.innerText))continue; button.click();count++;}return {count}})()`):null;
  await sleep(150);
  if(interacted)interacted.feedback=await evaluate(`[...document.querySelectorAll('.feedback')].map(e=>e.innerText).filter(Boolean).slice(0,3)`);
  reports.push({route,ready,...before,interacted,exceptions:[...exceptions]});
  console.log(JSON.stringify({route,ready,language:before.language,buttons:before.buttons,exceptions:exceptions.length,feedback:interacted?.feedback?.[0]}));
  if(lang==='ru'&&module===1){const image=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});fs.writeFileSync('preview-ru-module.png',Buffer.from(image.data,'base64'));}
 }
 fs.writeFileSync('course-check-report.json',JSON.stringify(reports,null,2));
 await send('Page.close');ws.close();
 if(reports.some(r=>!r.ready||r.exceptions.length||r.links.length))process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1;});
