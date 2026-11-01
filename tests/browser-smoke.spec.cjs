const {test,expect}=require('@playwright/test');
const sizes=[
  {width:360,height:780},
  {width:390,height:844},
  {width:1280,height:800},
];

for(const viewport of sizes){
  test('shared home and timeline remain usable at '+viewport.width+'px',async({browser})=>{
    const context=await browser.newContext({viewport,permissions:['clipboard-read','clipboard-write']});
    const page=await context.newPage();
    const pageErrors=[];
    page.on('pageerror',e=>pageErrors.push(e.message));
    for(const url of ['/index.html','/concepts.html','/study-history.html','/lectures/izYj8g-j00U.html#lecture-comment','/mini-courses/izYj8g-j00U.html','/summaries/izYj8g-j00U.html']){
      await page.goto(url);
      await expect(page.locator('main')).toBeVisible();
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-window.innerWidth);
      expect(overflow,'page overflow at '+url+' / '+viewport.width).toBeLessThanOrEqual(1);
    }
    await page.goto('/lectures/izYj8g-j00U.html#lecture-comment');
    const button=page.locator('[data-copy-target="comment"]');
    await expect(button).toBeVisible();
    const minHeight=await button.evaluate(el=>parseFloat(getComputedStyle(el).minHeight));
    expect(minHeight).toBeGreaterThanOrEqual(44);
    const source=await page.locator('#comment').textContent();
    await button.click();
    await expect(button).toHaveText('복사 완료 ✓');
    await expect(page.locator('#status')).toHaveText('복사됨');
    expect(await page.evaluate(()=>navigator.clipboard.readText())).toBe(source);
    await expect(button).toHaveText('댓글용 타임라인 복사',{timeout:6000});
    await expect(page.locator('#status')).toBeEmpty();
    expect(pageErrors).toEqual([]);
    await context.close();
  });
}

test('mobile header and card spacing remain compact',async({browser})=>{
  const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
  const page=await context.newPage();
  await page.goto('/index.html');
  const info=await page.evaluate(()=>{
    const header=document.querySelector('.site-header');
    const card=document.querySelector('.lecture');
    const read=card.querySelector('.read');
    const color=getComputedStyle(header).backgroundColor;
    const bottom=header.getBoundingClientRect().height;
    return {color,headerHeight:bottom,cardHeight:card.getBoundingClientRect().height,readMargin:parseFloat(getComputedStyle(read).marginTop)};
  });
  expect(info.color,'header must be opaque').toMatch(/^rgb\(/);
  expect(info.headerHeight,'mobile navigation should stay compact').toBeLessThan(115);
  expect(info.cardHeight,'cards should not stretch with empty space').toBeLessThan(400);
  expect(info.readMargin,'link spacing should not be auto').toBeLessThanOrEqual(14);
  await context.close();
});

test('main tabs load from static cache without a network connection',async({browser})=>{
  const context=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:'allow',reducedMotion:'reduce'});
  const page=await context.newPage();
  await page.goto('/index.html');
  await page.waitForFunction(async()=>{
    const registration=await navigator.serviceWorker.ready;
    if(!navigator.serviceWorker.controller || !registration.active)return false;
    const names=await caches.keys();
    const name=names.find(n=>n.startsWith('study-home-static-'));
    if(!name)return false;
    const cache=await caches.open(name);
    return (await Promise.all(['./index.html','./concepts.html','./study-history.html'].map(p=>cache.match(new URL(p,location.href))))).every(Boolean);
  },null,{timeout:15000});
  await context.setOffline(true);
  for(const [url,title] of [['/concepts.html','용어와 개념'],['/study-history.html','학습 이력'],['/index.html','강의 모음']]){
    await page.goto(url,{waitUntil:'domcontentloaded'});
    await expect(page.locator('.global-nav a[aria-current="page"]')).toHaveText(title);
    await expect(page.locator('main')).toBeVisible();
  }
  await context.close();
});
