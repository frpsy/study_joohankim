const {test,expect}=require('@playwright/test');
const version=require('../build-info.json').version;
test('PWA manifest, scoped paths and iPhone metadata are valid',async({page,request})=>{
  await page.goto('/index.html');
  await expect(page.locator('link[rel="manifest"]')).toHaveAttribute('href','manifest.webmanifest');
  await expect(page.locator('meta[name="viewport"]')).toHaveAttribute('content',/viewport-fit=cover/);
  await expect(page.locator('meta[name="apple-mobile-web-app-capable"]')).toHaveAttribute('content','yes');
  await expect(page.locator('link[rel="apple-touch-icon"]')).toHaveAttribute('sizes','180x180');
  const response=await request.get('/manifest.webmanifest');
  expect(response.ok()).toBe(true);
  const manifest=await response.json();
  expect(manifest.display).toBe('standalone');
  expect(manifest.id).toBe('/study_joohankim/');
  expect(manifest.scope).toBe('./');
  expect(manifest.start_url).toBe('./index.html');
  expect(manifest.icons.some(i=>i.sizes==='512x512' && i.purpose==='any')).toBe(true);
  for(const path of ['/assets/apple-touch-icon.png','/assets/icon-512.png','/offline.html']){
    expect((await request.get(path)).ok()).toBe(true);
  }
});
test('auto, manual dark and light theme persist across lectures and desktop',async({browser})=>{
  for(const width of [390,768,1280]){
    const context=await browser.newContext({viewport:{width,height:850},colorScheme:'dark'});
    const page=await context.newPage();
    await page.goto('/index.html');
    await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
    await expect(page.locator('html')).toHaveAttribute('data-theme-mode','auto');
    const dark=await page.locator('body').evaluate(e=>getComputedStyle(e).backgroundColor);
    await expect(page.locator('[data-theme-toggle]')).toHaveText('화면 · 시스템');
    await page.locator('[data-theme-toggle]').click();
    await expect(page.locator('html')).toHaveAttribute('data-theme','light');
    await expect(page.locator('[data-theme-toggle]')).toHaveText('화면 · 라이트');
    const light=await page.locator('body').evaluate(e=>getComputedStyle(e).backgroundColor);
    expect(light).not.toBe(dark);
    await page.goto('/lectures/affirmation-20261101.html');
    await expect(page.locator('html')).toHaveAttribute('data-theme','light');
    await page.locator('[data-theme-toggle]').click();
    await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
    await page.reload();
    await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
    const widths=await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth);
    expect(widths).toBeLessThanOrEqual(1);
    await page.locator('[data-theme-toggle]').click();
    await expect(page.locator('html')).toHaveAttribute('data-theme-mode','auto');
    await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
    await context.close();
  }
});
test('system appearance changes and keyboard operation remain accessible',async({browser})=>{
  const context=await browser.newContext({viewport:{width:1280,height:820},colorScheme:'light'});
  const page=await context.newPage();
  await page.goto('/lectures/affirmation-20261101.html');
  await expect(page.locator('html')).toHaveAttribute('data-theme','light');
  await page.emulateMedia({colorScheme:'dark'});
  await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
  const toggle=page.locator('[data-theme-toggle]');
  await toggle.focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('html')).toHaveAttribute('data-theme','light');
  await expect(toggle).toHaveAttribute('aria-label',/화면 테마/);
  await context.close();
});
test('standalone screen does not overflow and offline fallback is available',async({browser})=>{
  const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
  const page=await context.newPage();
  await page.addInitScript(()=>{Object.defineProperty(navigator,'standalone',{value:true,configurable:true})});
  await page.goto('/index.html');
  await expect(page.locator('html')).toHaveAttribute('data-standalone','true');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)).toBeLessThanOrEqual(1);
  await page.goto('/offline.html');
  await expect(page.getByRole('heading',{name:'인터넷에 연결되지 않았습니다'})).toBeVisible();
  await expect(page.locator('[data-theme-toggle]')).toBeVisible();
  await context.close();
});
test('service worker caches lecture library and app shell for offline reading',async({browser})=>{
  const context=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:'allow'});
  const page=await context.newPage();
  await page.goto('/index.html');
  const precache=await page.evaluate(async(version)=>{
    await navigator.serviceWorker.ready;
    const cachesList=await caches.keys();
    const name=cachesList.find(n=>n.includes('study-home-static-'+version));
    if(!name)return {name:null,lecture:false,theme:false};
    const cache=await caches.open(name);
    const url=p=>new URL(p,location.href).href;
    return {name,lecture:!!(await cache.match(url('lectures/affirmation-20261101.html'))),theme:!!(await cache.match(url('assets/theme.js')))};
  },version);
  expect(precache.name).toBeTruthy();
  expect(precache.lecture).toBe(true);
  expect(precache.theme).toBe(true);
  await context.setOffline(true);
  if(browser.browserType().name()==='webkit'){
    // Playwright's Linux WebKit can throw an internal error on offline page.goto.
    // Verify the same cached document bytes through CacheStorage; Chromium tests navigation.
    const cached=await page.evaluate(async()=>{
      const cache=await caches.open((await caches.keys()).find(x=>x.startsWith('study-home-static-')));
      const result=await cache.match(new URL('lectures/affirmation-20261101.html',location.href));
      return result?.ok && (await result.text()).includes('자기확언');
    });
    expect(cached).toBe(true);
  }else{
    await page.goto('/lectures/affirmation-20261101.html');
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('html')).toHaveAttribute('data-theme',/^(dark|light)$/);
  }
  await context.close();
});

test('appearance control is quiet and only at bottom of every page',async({browser})=>{
 for(const width of [360,390,768,1280]){
  const context=await browser.newContext({viewport:{width,height:844},colorScheme:'dark'});
  const page=await context.newPage();
  for(const url of ['/index.html','/lectures/affirmation-20261101.html','/offline.html']){
   await page.goto(url);
   await expect(page.locator('.site-header [data-theme-toggle]')).toHaveCount(0);
   await expect(page.locator('.site-footer-inner [data-theme-toggle]')).toHaveCount(1);
   const styles=await page.locator('.site-footer-inner [data-theme-toggle]').evaluate(el=>({
     font:parseFloat(getComputedStyle(el).fontSize),
     border:getComputedStyle(el).borderTopWidth,
     height:el.getBoundingClientRect().height,
     bottom:el.getBoundingClientRect().bottom,
     footer:el.closest('footer').getBoundingClientRect().bottom
   }));
   expect(styles.font).toBeLessThanOrEqual(12);
   expect(styles.border).toBe('0px');
   expect(styles.height).toBeGreaterThanOrEqual(44);
   expect(styles.bottom).toBeLessThanOrEqual(styles.footer);
   expect(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)).toBeLessThanOrEqual(1);
  }
  await page.goto('/index.html');
  await page.locator('.site-footer-inner [data-theme-toggle]').click();
  await expect(page.locator('html')).toHaveAttribute('data-theme','light');
  await context.close();
 }
});

test('online navigation rejects a stale cached header and offline still reads the page',async({browser})=>{
  const context=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:'allow'});
  const page=await context.newPage();
  await page.goto('/index.html');
  await page.evaluate(async()=>{
    await navigator.serviceWorker.ready;
    const registration=await navigator.serviceWorker.getRegistration();
    await registration.update();
  });
  await page.reload();
  await expect(page.locator('.site-header [data-theme-toggle]')).toHaveCount(0);
  await expect(page.locator('.site-footer [data-theme-toggle]')).toHaveCount(1);
  await page.evaluate(async()=>{
    const key=(await caches.keys()).find(k=>k.startsWith('study-home-static-'));
    const cache=await caches.open(key);
    const stale='<!doctype html><html><body><header class="site-header"><button data-theme-toggle>OLD HEADER BUTTON</button></header><main>old offline document</main></body></html>';
    await cache.put(new URL('index.html',location.href),new Response(stale,{headers:{'Content-Type':'text/html;charset=UTF-8'}}));
  });
  await page.goto('/index.html?check=online-first');
  await expect(page.locator('.site-header [data-theme-toggle]')).toHaveCount(0);
  await expect(page.locator('.site-footer [data-theme-toggle]')).toHaveCount(1);
  await expect(page.locator('h1')).toHaveText('강의 요약');
  const freshCached=await page.evaluate(async()=>{
    const key=(await caches.keys()).find(k=>k.startsWith('study-home-static-'));
    const cache=await caches.open(key);
    const response=await cache.match(new URL('index.html',location.href));
    return response ? (await response.text()).includes('OLD HEADER BUTTON') : true;
  });
  expect(freshCached).toBe(false);
  await context.setOffline(true);
  if(browser.browserType().name()==='webkit'){
    // Linux Playwright WebKit errors on page.goto while offline; verify fresh cached bytes.
    const cached=await page.evaluate(async()=>{
      const key=(await caches.keys()).find(k=>k.startsWith('study-home-static-'));
      const response=await (await caches.open(key)).match(new URL('index.html',location.href));
      return response ? (await response.text()).includes('<h1 class="home-title">강의 요약</h1>') : false;
    });
    expect(cached).toBe(true);
  }else{
    await page.goto('/index.html');
    await expect(page.locator('h1')).toHaveText('강의 요약');
  }
  await context.close();
});
