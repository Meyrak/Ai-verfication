/* Translate presentation text only. Quiz data, answer values and event handlers stay intact. */
(() => {
  const script = document.currentScript;
  const dictionaryUrl = script.dataset.dictionary;
  const locale = script.dataset.locale;
  document.documentElement.lang = locale;
  window.courseLocalizationReady = fetch(dictionaryUrl).then(response => {
    if (!response.ok) throw new Error('Course translation could not be loaded');
    return response.json();
  }).then(dictionary => {
    const pairs = Object.entries(dictionary).filter(([source,target]) => source !== target && target);
    const exact = new Map(pairs);
    const escapeRegex = value => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const pattern = new RegExp(pairs.map(([source]) => source).sort((a,b) => b.length-a.length).map(source => '(?<![\\p{L}\\p{N}_])'+escapeRegex(source)+'(?![\\p{L}\\p{N}_])').join('|'), 'gu');
    const previous = new WeakMap();
    const translate = text => {
      const trimmed=text.trim();
      if (exact.has(trimmed)) return text.replace(trimmed,exact.get(trimmed));
      return text.replace(pattern,source=>exact.get(source));
    };
    const visit = node => {
      if (node.nodeType === Node.TEXT_NODE) {
        if (node.parentElement?.closest('script,style,svg,code,pre,.course-navigation,.course-translation-note')) return;
        const source=node.nodeValue;
        if (previous.get(node)===source) return;
        const translated=translate(source);
        previous.set(node,translated);
        if (translated!==source) node.nodeValue=translated;
      } else if (node.nodeType === Node.ELEMENT_NODE || node.nodeType === Node.DOCUMENT_NODE) {
        if (node.matches?.('script,style,svg,code,pre,.course-navigation,.course-translation-note')) return;
        if (node.hasAttribute?.('placeholder')) node.setAttribute('placeholder',translate(node.getAttribute('placeholder')));
        if (node.hasAttribute?.('aria-label')) node.setAttribute('aria-label',translate(node.getAttribute('aria-label')));
        Array.from(node.childNodes).forEach(visit);
      }
    };
    visit(document.documentElement);
    new MutationObserver(records => {
      records.forEach(record => {
        if (record.type==='characterData') visit(record.target);
        else record.addedNodes.forEach(visit);
      });
    }).observe(document.documentElement,{subtree:true,childList:true,characterData:true});
    document.documentElement.dataset.courseTranslated=locale;
    return true;
  }).catch(error => {console.error(error); return false;});
})();
