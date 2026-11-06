/* Apply saved appearance before CSS paints. No account or learning data is stored. */
(()=>{
  'use strict';
  const key='study-site-appearance';
  if(navigator.standalone === true || window.matchMedia('(display-mode: standalone)').matches)document.documentElement.dataset.standalone='true';
  const media=window.matchMedia('(prefers-color-scheme: dark)');
  const modes=['auto','light','dark'];
  let choice='auto';
  try{const stored=localStorage.getItem(key);if(modes.includes(stored))choice=stored}catch{}
  const active=()=>choice==='auto'?(media.matches?'dark':'light'):choice;
  const labels={auto:'시스템',light:'라이트',dark:'다크'};
  const apply=()=>{
    const theme=active();
    document.documentElement.dataset.theme=theme;
    document.documentElement.dataset.themeMode=choice;
    document.documentElement.style.colorScheme=theme;
    const bar=document.querySelector('meta[name="theme-color"]');
    if(bar)bar.content=theme==='dark'?'#0b0b0c':'#ffffff';
    const button=document.querySelector('[data-theme-toggle]');
    if(button){
      const next=modes[(modes.indexOf(choice)+1)%modes.length];
      button.textContent='화면 · '+labels[choice];
      button.setAttribute('aria-label','화면 테마: '+labels[choice]+'. 누르면 '+labels[next]+' 모드');
      button.title='화면 테마: '+labels[choice];
    }
  };
  apply();
  const initialize=()=>{
    apply();
    const button=document.querySelector('[data-theme-toggle]');
    button?.addEventListener('click',()=>{
      choice=modes[(modes.indexOf(choice)+1)%modes.length];
      try{if(choice==='auto')localStorage.removeItem(key);else localStorage.setItem(key,choice)}catch{}
      apply();
    });
  };
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initialize,{once:true});
  else initialize();
  const systemChange=()=>{if(choice==='auto')apply()};
  if(media.addEventListener)media.addEventListener('change',systemChange);
  else if(media.addListener)media.addListener(systemChange);
})();
