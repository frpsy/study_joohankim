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
  await page.goto('/concepts.html');
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
  await page.goto('/lectures/affirmation-20261101.html');
  await expect(page.locator('h1')).toBeVisible();
  await expect(page.locator('html')).toHaveAttribute('data-theme',/^(dark|light)$/);
  await context.close();
});
