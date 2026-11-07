const {test,expect}=require('@playwright/test');
const studyVersion=require('../build-info.json').version;
const studyLectures=require('../lectures.json');
const studyMaterials=require('../materials.json');
const expectedLibraryCount=studyLectures.length+studyMaterials.length;
const kimLectureCount=studyLectures.filter(x=>x.creator==='김주환').length;
const sizes=[
  {width:360,height:780},
  {width:390,height:844},
  {width:768,height:900},
  {width:1280,height:800},
];

for(const viewport of sizes){
  test('shared home and timestamps remain usable at '+viewport.width+'px',async({browser})=>{
    const context=await browser.newContext({viewport,permissions:['clipboard-read','clipboard-write']});
    const page=await context.newPage();
    const pageErrors=[];
    page.on('pageerror',e=>pageErrors.push(e.message));
    for(const url of ['/index.html',...studyLectures.map(x=>'/lectures/'+x.id+'.html')]){
      await page.goto(url);
      await expect(page.locator('main')).toBeVisible();
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-window.innerWidth);
      expect(overflow,'page overflow at '+url+' / '+viewport.width).toBeLessThanOrEqual(1);
    }
    await page.goto('/lectures/izYj8g-j00U.html#lecture-comment');
    const button=page.locator('[data-copy-target="comment"]');
    await expect(button).toBeVisible();
    await expect(button).toHaveText('타임스탬프 복사');
    const minHeight=await button.evaluate(el=>parseFloat(getComputedStyle(el).minHeight));
    expect(minHeight).toBeGreaterThanOrEqual(44);
    const comment=page.locator('#comment');
    const toggle=page.locator('#timeline-toggle');
    await expect(page.getByText('전체 타임스탬프 보기')).toHaveCount(0);
    await expect(comment).toBeVisible();
    const collapsed=await comment.evaluate(el=>({box:el.getBoundingClientRect().height,scrolls:el.scrollHeight>el.clientHeight+1}));
    expect(collapsed.box).toBeLessThan(330);
    expect(collapsed.scrolls,'collapsed timestamp box scrolls').toBe(true);
    await comment.click();
    await expect(toggle).toBeChecked();
    const expanded=await comment.evaluate(el=>({box:el.getBoundingClientRect().height,scrolls:el.scrollHeight>el.clientHeight+1}));
    expect(expanded.box).toBeGreaterThan(collapsed.box+100);
    expect(expanded.scrolls,'expanded timestamp box shows everything').toBe(false);
    await comment.click();
    await expect(toggle).not.toBeChecked();
    const source=await page.locator('#comment').textContent();
    await button.click();
    await expect(button).toHaveText('복사 완료 ✓');
    await expect(page.locator('#status')).toHaveText('복사됨');
    expect(await page.evaluate(()=>navigator.clipboard.readText())).toBe(source);
    await expect(button).toHaveText('타임스탬프 복사',{timeout:6000});
    await expect(page.locator('#status')).toBeEmpty();
    expect(pageErrors).toEqual([]);
    await context.close();
  });
}

test('glass header stays legible and cards stay compact on mobile',async({browser})=>{
  const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
  const page=await context.newPage();
  await page.goto('/index.html');
  const info=await page.evaluate(()=>{
    const header=document.querySelector('.site-header');
    const card=document.querySelector('.lecture');
    const read=card.querySelector('.read');
    const style=getComputedStyle(header);
    const match=style.backgroundColor.match(/rgba?\(([^)]+)\)/);
    const parts=match?match[1].split(',').map(Number):[];
    return {alpha:parts.length===4?parts[3]:1,blur:(style.backdropFilter||style.webkitBackdropFilter||''),headerHeight:header.getBoundingClientRect().height,cardHeight:card.getBoundingClientRect().height,readMargin:parseFloat(getComputedStyle(read).marginTop)};
  });
  expect(info.alpha,'translucent header must keep enough opacity to stay legible').toBeGreaterThanOrEqual(0.7);
  if(info.alpha<1)expect(info.blur,'translucent header needs a backdrop blur').toContain('blur');
  expect(info.headerHeight,'mobile header should stay compact').toBeLessThan(80);
  expect(info.cardHeight,'cards should not stretch with empty space').toBeLessThan(400);
  expect(info.readMargin,'link spacing should not be auto').toBeLessThanOrEqual(14);
  await context.close();
});

test('home and lectures load from static cache without a network connection',async({browser})=>{
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
    return (await Promise.all(['./index.html','./lectures/izYj8g-j00U.html'].map(p=>cache.match(new URL(p,location.href))))).every(Boolean);
  },null,{timeout:15000});
  await context.setOffline(true);
  await page.goto('/lectures/izYj8g-j00U.html',{waitUntil:'domcontentloaded'});
  await expect(page.locator('#lecture-overview')).toBeVisible();
  await page.goto('/index.html',{waitUntil:'domcontentloaded'});
  await expect(page.locator('h1')).toHaveText('강의 요약');
  await context.close();
});

test('footer shows actual loaded version and checks deployed version separately',async({browser})=>{
  const context=await browser.newContext({viewport:{width:390,height:844}});
  const page=await context.newPage();
  await page.goto('/index.html');
  await expect(page.locator('.site-version')).toContainText('화면 v'+studyVersion);
  await expect(page.locator('.site-version')).toContainText('최신 버전');
  await context.close();
});
test('footer provides a refresh link when deployed manifest is newer',async({browser})=>{
  const context=await browser.newContext();
  const page=await context.newPage();
  await page.route('**/build-info.json*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({version:'2099.01.01.1'})}));
  await page.goto('/index.html');
  await expect(page.locator('.site-version')).toContainText('최신 v2099.01.01.1');
  await expect(page.locator('.site-version a')).toHaveAttribute('href',/refresh=2099.01.01.1/);
  await context.close();
});

test('login, record saving, and history UI are absent',async({page})=>{
 await page.goto('/index.html');
 for(const selector of ['#settings','#settings-toggle','#account-action','#account-history','#study-progress']){
  await expect(page.locator(selector)).toHaveCount(0);
 }
 await expect(page.getByRole('link',{name:'학습 이력'})).toHaveCount(0);
 await page.goto('/lectures/affirmation-20261101.html');
 await expect(page.locator('#study-progress')).toHaveCount(0);
 await expect(page.getByRole('button',{name:/학습 완료|복습 완료/})).toHaveCount(0);
 await expect(page.locator('#lecture-overview')).toBeVisible();
});

test('library identity and reading hierarchy stay consistent',async({browser})=>{
  const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
  const page=await context.newPage();
  for(const url of ['/index.html','/lectures/izYj8g-j00U.html']){
    await page.goto(url);
    await expect(page.locator('.site-brand .brand-name')).toContainText('내면의 서재');
    await expect(page.locator('.brand-symbol')).toBeVisible();
    expect(await page.locator('.brand-symbol').evaluate(el=>el.naturalWidth)).toBeGreaterThan(0);
    await expect(page).toHaveTitle(/내면의 서재/);
    await expect(page.locator('.global-nav')).toHaveCount(0);
    const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth);
    expect(overflow,'no horizontal overflow at '+url).toBeLessThanOrEqual(1);
  }
  await page.goto('/index.html');
  await expect(page.locator('.home-title')).toHaveText('강의 요약');
  const compact=await page.evaluate(()=>({
    headerHeight:document.querySelector('.site-header').getBoundingClientRect().height,
    titleHeight:document.querySelector('.home-title').getBoundingClientRect().height,
    cardCount:document.querySelectorAll('#home-catalog [data-kind]').length,
  }));
  expect(compact.headerHeight).toBeLessThan(80);
  expect(compact.titleHeight).toBeLessThan(95);
  expect(compact.cardCount).toBe(expectedLibraryCount);
  await page.locator('[data-filter-for="search"][data-value="명상"]').click();
  await expect(page.locator('#count')).toHaveText('1개 강의');
  await expect(page.locator('#lecture-list .lecture:visible')).toHaveCount(1);
  await context.close();
});

test('home lists every lecture in one aligned column',async({browser})=>{
  for(const width of [360,390,768,1280]){
    const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
    const page=await context.newPage();
    await page.goto('/index.html');
    const m=await page.evaluate(()=>{
      const rect=el=>el.getBoundingClientRect();
      const cards=[...document.querySelectorAll('#lecture-list .lecture')].map(rect);
      return {lefts:[...new Set(cards.map(r=>Math.round(r.left)))],rights:cards.map(r=>r.right),width:cards[0].width,
        brand:rect(document.querySelector('.site-brand')).left,title:rect(document.querySelector('.home-title')).left,
        overflow:document.documentElement.scrollWidth-innerWidth};
    });
    expect(m.lefts).toHaveLength(1);
    expect(Math.abs(m.brand-m.title)).toBeLessThanOrEqual(1);
    expect(Math.abs(m.lefts[0]-m.title)).toBeLessThanOrEqual(1);
    expect(Math.max(...m.rights)).toBeLessThanOrEqual(width);
    expect(m.width).toBeGreaterThan(width<=780?width-40:700);
    expect(m.overflow).toBeLessThanOrEqual(1);
    await context.close();
  }
});

test('catalog searches by creator without losing video ID hooks',async({page})=>{
  await page.goto('/index.html');
  const items=page.locator('#lecture-list .lecture');
  await expect(items).toHaveCount(expectedLibraryCount);
  await expect(page.locator('[data-creator="Andrew Huberman"]')).toHaveCount(2);
  await page.locator('#search').fill('Huberman');
  await expect(page.locator('#count')).toHaveText('2개 강의');
  await expect(page.locator('#lecture-list .lecture:visible')).toHaveCount(2);
  await expect(page.locator('#lecture-list .lecture[data-video-id="QmOF0crdyRU"]')).toBeVisible();
  await expect(page.locator('#lecture-list .lecture[data-video-id="9tRohh0gErM"]')).toBeVisible();
  await page.locator('#search').fill('김주환');
  await expect(page.locator('#count')).toHaveText(kimLectureCount+'개 강의');
});

test('catalog restores a shared search and returns to it after reading',async({page})=>{
  await page.goto('/index.html?q=Huberman&source=test#lectures');
  await expect(page.locator('#search')).toHaveValue('Huberman');
  await expect(page.locator('#lecture-list .lecture:visible')).toHaveCount(2);
  await page.locator('#lecture-list .lecture:visible').first().click();
  await page.goBack();
  await expect(page.locator('#search')).toHaveValue('Huberman');
  await expect(page.locator('#count')).toHaveText('2개 강의');
  await page.locator('#search').fill('없는검색어');
  await expect(page.locator('#empty')).toBeVisible();
  await expect(page).toHaveURL(/q=/);
  await page.locator('[data-clear-for="search"]').click();
  await expect(page.locator('#search')).toBeFocused();
  await expect(page.locator('#search')).toHaveValue('');
  await expect(page.locator('#count')).toHaveText(expectedLibraryCount+'개 강의');
  expect(new URL(page.url()).searchParams.has('q')).toBe(false);
  expect(new URL(page.url()).searchParams.get('source')).toBe('test');
  await page.locator('[data-filter-for="search"][data-value="수용"]').click();
  expect(new URL(page.url()).searchParams.get('q')).toBe('수용');
  await page.reload();
  await expect(page.locator('#count')).toHaveText('1개 강의');
  await expect(page.locator('[data-filter-for="search"][data-value="수용"]')).toHaveAttribute('aria-pressed','true');
});

test('a lecture card opens a page with only the key summary and timestamps',async({page})=>{
  await page.goto('/index.html');
  await page.locator('#lecture-list [data-video-id="affirmation-20261101"]').click();
  await expect(page).toHaveURL(/\/lectures\/affirmation-20261101\.html$/);
  await expect(page.locator('main .lecture-section')).toHaveCount(2);
  await expect(page.locator('#lecture-overview>h2')).toHaveText('핵심 요약');
  await expect(page.locator('#lecture-comment>h2')).toHaveText('타임스탬프');
  for(const removed of ['5분 요약','미니강좌','용어와 개념']){
    await expect(page.getByText(removed)).toHaveCount(0);
  }
  await page.locator('.summary-links a').click();
  await expect(page).toHaveURL(/\/index\.html$/);
});

test('lecture summary keeps a clear type hierarchy and readable width',async({browser})=>{
  for(const width of [360,390,768,1280]){
    const context=await browser.newContext({viewport:{width,height:844},reducedMotion:'reduce'});
    const page=await context.newPage();
    await page.goto('/lectures/affirmation-20261101.html');
    await expect(page.locator('#lecture-overview .summary-tier>h3')).toHaveText('핵심 세 가지');
    await expect(page.locator('#lecture-overview .summary-list li')).toHaveCount(3);
    const m=await page.evaluate(()=>{
      const size=selector=>parseFloat(getComputedStyle(document.querySelector(selector)).fontSize);
      const box=document.querySelector('.compact-lecture').getBoundingClientRect();
      return {h1:size('h1'),h2:size('#lecture-overview>h2'),h3:size('#lecture-overview .summary-tier>h3'),
        lead:size('#lecture-overview .summary-tier>.summary-lead'),list:size('#lecture-overview .summary-list li'),
        width:box.width,left:box.left,right:box.right,brand:document.querySelector('.site-brand').getBoundingClientRect().left,
        overflow:document.documentElement.scrollWidth-window.innerWidth};
    });
    expect(m.h1).toBeGreaterThan(m.h2);
    expect(m.h2).toBeGreaterThan(m.h3);
    expect(m.h3).toBeGreaterThanOrEqual(m.list);
    expect(m.list).toBeLessThanOrEqual(16);
    expect(m.lead).toBeLessThanOrEqual(17);
    expect(m.width).toBeLessThanOrEqual(width<=780 ? width-24 : 761);
    expect(m.left).toBeGreaterThanOrEqual(width<=780 ? 12 : -1);
    expect(Math.abs(m.left-m.brand)).toBeLessThanOrEqual(1);
    expect(m.overflow).toBeLessThanOrEqual(1);
    await context.close();
  }
});
