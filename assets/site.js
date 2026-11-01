/* Shared navigation and discovery. Lecture-specific copy/checkbox logic stays in its page. */
(()=>{
  const header=document.querySelector('.site-header');
  const sidebar=document.querySelector('.sidebar');
  function syncNavigationSize(){
    const headerHeight=header ? header.getBoundingClientRect().height : 0;
    const mobile=window.matchMedia('(max-width:780px)').matches;
    const sidebarHeight=mobile && sidebar ? sidebar.getBoundingClientRect().height : 0;
    document.documentElement.style.setProperty('--header-height',headerHeight+'px');
    document.documentElement.style.setProperty('--anchor-offset',(headerHeight+sidebarHeight+16)+'px');
  }
  syncNavigationSize();
  window.addEventListener('resize',syncNavigationSize);
  if('ResizeObserver' in window){
    const sizes=new ResizeObserver(syncNavigationSize);
    if(header)sizes.observe(header);
    if(sidebar)sizes.observe(sidebar);
  }
  function revealAnchor(){
    let id;try{id=decodeURIComponent(location.hash.slice(1))}catch{return}if(!id)return;
    const target=document.getElementById(id);if(!target)return;
    for(let parent=target;parent;parent=parent.parentElement)if(parent.tagName==='DETAILS')parent.open=true;
    if(target.tagName==='SUMMARY')target.parentElement.open=true;
    target.scrollIntoView({block:'start'});
  }
  window.addEventListener('hashchange',revealAnchor);
  if(location.hash)revealAnchor();
  const links=[...document.querySelectorAll('.sidebar a[href^="#"]')];
  if('IntersectionObserver' in window){
    const observer=new IntersectionObserver(entries=>{
      const visible=entries.filter(e=>e.isIntersecting).sort((a,b)=>a.boundingClientRect.top-b.boundingClientRect.top)[0];
      if(!visible)return;
      links.forEach(a=>{if(a.hash==='#'+visible.target.id)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current')});
    },{rootMargin:'-110px 0px -55% 0px'});
    links.forEach(a=>{const el=document.getElementById(a.hash.slice(1));if(el)observer.observe(el)});
  }
  document.querySelectorAll('[data-filter-input]').forEach(input=>{
    const target=document.querySelector(input.dataset.filterInput);if(!target)return;
    const cards=[...target.querySelectorAll('[data-search]')];
    const count=document.getElementById(input.dataset.count),empty=document.getElementById(input.dataset.empty);
    const filter=()=>{
      const words=input.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);let shown=0;
      cards.forEach(card=>{const hay=(card.textContent+' '+card.dataset.search).toLocaleLowerCase();card.hidden=!words.every(word=>hay.includes(word));if(!card.hidden)shown++});
      if(count)count.textContent=shown+'개 '+input.dataset.noun;
      if(empty)empty.hidden=shown!==0;
      document.querySelectorAll('[data-filter-for="'+input.id+'"]').forEach(button=>{
        button.setAttribute('aria-pressed',String((button.dataset.value||'')===input.value.trim()));
      });
    };
    const query=new URLSearchParams(location.search).get('q');if(query)input.value=query;
    input.addEventListener('input',filter);filter();
    document.querySelectorAll('[data-filter-for="'+input.id+'"]').forEach(button=>button.addEventListener('click',()=>{input.value=button.dataset.value||'';filter();button.blur()}));
  });
  document.querySelectorAll('[data-copy-target]').forEach(button=>{
    const originalLabel=button.textContent.trim();
    let resetTimer;
    button.addEventListener('click',async()=>{
      const source=document.getElementById(button.dataset.copyTarget);
      const status=button.parentElement.querySelector('[role="status"]')||document.getElementById('status');
      if(!source)return;
      clearTimeout(resetTimer);
      try{
        if(!navigator.clipboard?.writeText)throw new Error('Clipboard API unavailable');
        await navigator.clipboard.writeText(source.textContent);
        button.textContent='복사 완료 ✓';
        if(status)status.textContent='복사됨';
      }catch{
        const selection=window.getSelection(),range=document.createRange();
        range.selectNodeContents(source);selection.removeAllRanges();selection.addRange(range);
        button.textContent='텍스트 선택됨';
        if(status)status.textContent='선택한 내용을 직접 복사해 주세요.';
      }
      resetTimer=setTimeout(()=>{button.textContent=originalLabel;if(status)status.textContent=''},2200);
    });
  });
  document.querySelectorAll('[data-timeline-toggle]').forEach(button=>{
    const source=document.getElementById(button.dataset.timelineToggle);
    if(!source)return;
    button.addEventListener('click',()=>{
      const expanded=source.classList.toggle('is-expanded');
      button.setAttribute('aria-expanded',String(expanded));
      button.textContent=expanded?'접기':'전체 보기';
    });
  });
  document.querySelectorAll('[data-expand-scope]').forEach(button=>button.addEventListener('click',()=>{
    document.querySelectorAll(button.dataset.expandScope+' details').forEach(d=>d.open=button.dataset.expand==='true');
  }));

  // Cache only public same-origin study pages and common assets. Other origins
  // (Firebase Auth / Firestore) are deliberately outside the worker's scope.
  if ('serviceWorker' in navigator && (location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1')) {
    const assetScript = document.currentScript;
    if (assetScript?.src) {
      const workerURL = new URL('../sw.js', assetScript.src);
      navigator.serviceWorker.register(workerURL.href).catch(() => {});
    }
  }
})();
