/* Shared navigation and discovery. Lecture-specific copy/checkbox logic stays in its page. */
(()=>{
  function revealAnchor(){
    const id=decodeURIComponent(location.hash.slice(1));if(!id)return;
    const target=document.getElementById(id);if(!target)return;
    for(let parent=target.parentElement;parent;parent=parent.parentElement)if(parent.tagName==='DETAILS')parent.open=true;
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
    };
    const query=new URLSearchParams(location.search).get('q');if(query)input.value=query;
    input.addEventListener('input',filter);filter();
    document.querySelectorAll('[data-filter-for="'+input.id+'"]').forEach(button=>button.addEventListener('click',()=>{input.value=button.dataset.value||'';filter();input.focus()}));
  });
  document.querySelectorAll('[data-expand-scope]').forEach(button=>button.addEventListener('click',()=>{
    document.querySelectorAll(button.dataset.expandScope+' details').forEach(d=>d.open=button.dataset.expand==='true');
  }));
})();
