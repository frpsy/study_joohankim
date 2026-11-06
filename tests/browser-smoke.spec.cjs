const {test,expect}=require('@playwright/test');
const studyVersion=require('../build-info.json').version;
const studyLectures=require('../lectures.json');
const studyMaterials=require('../materials.json');
const expectedLibraryCount=studyLectures.length+studyMaterials.length;
const kimLectureCount=studyLectures.filter(x=>x.creator==='김주환').length;
const sizes=[
  {width:360,height:780},
  {width:375,height:812},
  {width:390,height:844},
  {width:768,height:900},
  {width:1280,height:800},
];

for(const viewport of sizes){
  test('shared home and timeline remain usable at '+viewport.width+'px',async({browser})=>{
    const context=await browser.newContext({viewport,permissions:['clipboard-read','clipboard-write']});
    const page=await context.newPage();
    const pageErrors=[];
    page.on('pageerror',e=>pageErrors.push(e.message));
    for(const url of ['/index.html','/concepts.html','/lectures/izYj8g-j00U.html#lecture-comment','/mini-courses/izYj8g-j00U.html','/summaries/izYj8g-j00U.html']){
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
    const disclosure=page.locator('details.timeline-disclosure');
    await expect(disclosure).not.toHaveAttribute('open');
    await expect(disclosure.locator('summary')).toHaveText('펼치기접기');
    const teaser=page.locator('.timeline-teaser');
    await expect(teaser).toBeVisible();
    const lines=(await teaser.textContent()).split('\n');
    expect(lines).toHaveLength(3);
    expect(lines).toEqual((await page.locator('#comment').textContent()).split('\n').slice(0,3));
    await expect(page.locator('#comment')).toBeHidden();
    expect(await disclosure.evaluate(el=>el.getBoundingClientRect().height)).toBeLessThan(55);
    await disclosure.locator('summary').click();
    await expect(disclosure).toHaveAttribute('open');
    await expect(page.locator('#comment')).toBeVisible();
    await expect(disclosure.getByText('접기',{exact:true})).toBeVisible();
    await expect(teaser).toBeHidden();
    await disclosure.locator('summary').click();
    await expect(disclosure).not.toHaveAttribute('open');
    await expect(page.locator('#comment')).toBeHidden();
    const source=await page.locator('#comment').textContent();
    await button.click();
    await expect(button).toHaveText('복사 완료 ✓');
    await expect(page.locator('#status')).toHaveText('복사됨');
    expect(await page.evaluate(()=>navigator.clipboard.readText())).toBe(source);
    await expect(button).toHaveText('복사',{timeout:6000});
    await expect(page.locator('#status')).toBeEmpty();
    expect(pageErrors).toEqual([]);
    await context.close();
  });
}

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
    return (await Promise.all(['./index.html','./concepts.html','./mini-courses/index.html'].map(p=>cache.match(new URL(p,location.href))))).every(Boolean);
  },null,{timeout:15000});
  await context.setOffline(true);
  for(const [url,title] of [['/concepts.html','용어와 개념'],['/mini-courses/index.html','미니강좌'],['/index.html','강의']]){
    await page.goto(url,{waitUntil:'domcontentloaded'});
    await expect(page.locator('.global-nav a[aria-current="page"]')).toHaveText(title);
    await expect(page.locator('main')).toBeVisible();
  }
  await context.close();
});

test('footer shows actual loaded version and checks deployed version separately',async({browser})=>{
  const context=await browser.newContext({viewport:{width:390,height:844}});
  const page=await context.newPage();
  await page.goto('/index.html');
  await expect(page.locator('.site-version')).toContainText('화면 v'+studyVersion);
  await expect(page.locator('.site-version')).toContainText('최신 배포 확인');
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

test('editorial library identity and reading hierarchy stay consistent',async({browser})=>{
  const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
  const page=await context.newPage();
  for(const url of ['/index.html','/concepts.html','/lectures/izYj8g-j00U.html']){
    await page.goto(url);
    await expect(page.locator('.site-brand .brand-name')).toContainText('김주환 강의 스터디');
    await expect(page.locator('.brand-symbol')).toBeVisible();
    expect(await page.locator('.brand-symbol').evaluate(el=>el.naturalWidth)).toBeGreaterThan(0);
    await expect(page).toHaveTitle(/김주환 강의 스터디/);
    const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth);
    expect(overflow,'no horizontal overflow at '+url).toBeLessThanOrEqual(1);
  }
  await page.goto('/index.html');
  await expect(page.locator('.home-main h1')).toHaveText('김주환 강의 스터디');
  const compact=await page.evaluate(()=>{
    const header=document.querySelector('.site-header').getBoundingClientRect();
    const title=document.querySelector('.home-main h1').getBoundingClientRect();
    const cards=[...document.querySelectorAll('#lecture-list [data-kind]')];
    const items=[...document.querySelectorAll('.global-nav a')];
    return {headerHeight:header.height,titleHeight:title.height,cardCount:cards.length,
      menuTapHeight:Math.min(...items.map(el=>el.getBoundingClientRect().height))};
  });
  expect(compact.headerHeight).toBeLessThan(115);
  expect(compact.titleHeight).toBeLessThan(95);
  expect(compact.cardCount).toBe(expectedLibraryCount);
  expect(compact.menuTapHeight).toBeGreaterThanOrEqual(44);
  await page.locator('[data-filter-for="search"][data-value="명상"]').click();
  await expect(page.locator('#count')).toHaveText('1개 자료');
  await expect(page.locator('#lecture-list .lecture-row:visible')).toHaveCount(1);
  await context.close();
});

test('catalog searches by creator without losing video ID progress hooks',async({page})=>{
  await page.goto('/index.html');
  const items=page.locator('#lecture-list .lecture-row');
  await expect(items).toHaveCount(expectedLibraryCount);
  await expect(page.locator('[data-creator="Andrew Huberman"]')).toHaveCount(1);
  await page.locator('#search').fill('Huberman');
  await expect(page.locator('#count')).toHaveText('1개 자료');
  await expect(page.locator('#lecture-list .lecture-row:visible')).toHaveCount(1);
  await expect(page.locator('#lecture-list .lecture-row:visible')).toHaveAttribute('data-video-id','QmOF0crdyRU');
  await page.locator('#search').fill('김주환');
  await expect(page.locator('#count')).toHaveText(kimLectureCount+'개 자료');
});

test('catalog restores a shared search and returns to it after reading',async({page})=>{
  await page.goto('/index.html?q=Huberman&source=test#lectures');
  await expect(page.locator('#search')).toHaveValue('Huberman');
  await expect(page.locator('#lecture-list .lecture-row:visible')).toHaveCount(1);
  await page.locator('#lecture-list .lecture-row:visible').click();
  await page.goBack();
  await expect(page.locator('#search')).toHaveValue('Huberman');
  await expect(page.locator('#count')).toHaveText('1개 자료');
  await page.locator('#search').fill('없는검색어');
  await expect(page.locator('#empty')).toBeVisible();
  await expect(page).toHaveURL(/q=/);
  await page.locator('[data-clear-for="search"]').click();
  await expect(page.locator('#search')).toBeFocused();
  await expect(page.locator('#search')).toHaveValue('');
  await expect(page.locator('#count')).toHaveText(expectedLibraryCount+'개 자료');
  expect(new URL(page.url()).searchParams.has('q')).toBe(false);
  expect(new URL(page.url()).searchParams.get('source')).toBe('test');
  await page.locator('[data-filter-for="search"][data-value="수용"]').click();
  expect(new URL(page.url()).searchParams.get('q')).toBe('수용');
  await page.reload();
  await expect(page.locator('#count')).toHaveText('1개 자료');
  await expect(page.locator('[data-filter-for="search"][data-value="수용"]')).toHaveAttribute('aria-pressed','true');
});

for(const width of [375,1280]){
 test('featured, topic search, no results and back navigation at '+width+'px',async({browser})=>{
  const context=await browser.newContext({viewport:{width,height:812}});
  const page=await context.newPage();
  await page.goto('/index.html');
  const feature=page.locator('.home-feature');
  const url='/lectures/affirmation-20261101.html#lecture-overview';
  const featureLinks=feature.getByRole('link');
  await expect(featureLinks).toHaveCount(2);
  for(const link of await featureLinks.all()){
   await expect(link).toHaveAttribute('href',url.slice(1));
   await link.click();
   await expect(page).toHaveURL(new RegExp(url+'$'));
   await expect(page.locator('#lecture-overview h2')).toBeInViewport();
   await page.goBack();
  }
  await page.locator('#search').fill('자기확언');
  await expect(page.locator('#lecture-list .lecture-row:visible')).toHaveCount(1);
  await page.locator('#lecture-list .lecture-row:visible').click();
  await expect(page.locator('#lecture-overview h2')).toBeInViewport();
  await page.goBack();
  await expect(page.locator('#search')).toHaveValue('자기확언');
  await page.getByRole('button',{name:'수용',exact:true}).click();
  await page.locator('#lecture-list .lecture-row:visible').click();
  await expect(page).toHaveURL(/ZCty0wvogDo\.html#lecture-overview$/);
  const timeline=page.locator('#lecture-details details');
  await timeline.locator('summary').click();
  await expect(timeline.getByRole('link').first()).toHaveAttribute('href',/watch\?v=ZCty0wvogDo&t=73$/);
  await expect(page.locator('#lecture-comment')).toContainText('한국어 자동자막 기반');
  await page.goBack();
  await expect(page.getByRole('button',{name:'수용',exact:true})).toHaveAttribute('aria-pressed','true');
  await page.locator('#search').fill('없는검색어');
  await expect(page.locator('#empty')).toBeVisible();
  await expect(page.locator('#count')).toHaveText('0개 자료');
  await expect(page.locator('#lecture-list .lecture-row:visible')).toHaveCount(0);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  const nav=page.getByRole('navigation',{name:'주요 메뉴'});
  await nav.getByRole('link',{name:'미니강좌'}).click();
  await expect(page.getByRole('heading',{name:'감정과 관계'})).toBeVisible();
  await nav.getByRole('link',{name:'용어와 개념'}).click();
  await expect(page.getByRole('heading',{name:'용어와 개념',exact:true})).toBeVisible();
  await context.close();
 });
}

test('mobile lecture summary uses clear type hierarchy and reader-facing labels',async({browser})=>{
  for(const width of [360,375,390,768,1280]){
    const context=await browser.newContext({viewport:{width,height:844}});
    const page=await context.newPage();
    await page.goto('/lectures/affirmation-20261101.html');
    await expect(page.locator('#lecture-overview>h2')).toHaveText('핵심 요약');
    await expect(page.locator('#lecture-overview .summary-tier:not(details)>h3')).toHaveText('02 · 핵심 3가지');
    await expect(page.locator('#lecture-overview .summary-list li')).toHaveCount(3);
    const metrics=await page.evaluate(()=>{
      const size=selector=>parseFloat(getComputedStyle(document.querySelector(selector)).fontSize);
      return {
        h2:size('#lecture-overview>h2'),
        h3:size('#lecture-overview .summary-tier:not(details)>h3'),
        lead:size('#lecture-overview .summary-tier>.summary-lead'),
        list:size('#lecture-overview .summary-list li'),
        overflow:document.documentElement.scrollWidth-window.innerWidth,
      };
    });
    expect(metrics.h2).toBeGreaterThan(metrics.h3);
    expect(metrics.h3).toBeGreaterThanOrEqual(metrics.list);
    expect(metrics.list).toBeLessThanOrEqual(16);
    expect(metrics.lead).toBeLessThanOrEqual(17);
    expect(metrics.overflow).toBeLessThanOrEqual(1);
    await page.goto('/mini-courses/affirmation-20261101.html');
    await expect(page.getByRole('link',{name:'핵심 요약'})).toBeVisible();
    await context.close();
  }
});

test('navigation and readable widths stay compact',async({browser})=>{
 for(const width of [360,375,390,768,1280]){
  const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
  const page=await context.newPage();
  await page.goto('/index.html');
  const metrics=await page.evaluate(()=>{
   const rect=selector=>{const x=document.querySelector(selector);const r=x.getBoundingClientRect();return {width:r.width,left:r.left,right:r.right,top:r.top,bottom:r.bottom}};
   const nav=document.querySelector('.global-nav');
   const tabs=[...nav.querySelectorAll('a')];
   return {
    tabCount:tabs.length,
    tabRects:tabs.map(x=>{const r=x.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,height:r.height}}),
    overview:rect('.home-main h1'),
    feature:rect('.home-feature'),
    card:rect('.lecture-row'),
    rootOverflow:document.documentElement.scrollWidth-innerWidth,
   };
  });
  expect(metrics.tabCount).toBe(3);
  expect(metrics.rootOverflow).toBeLessThanOrEqual(1);
  expect(metrics.feature.right).toBeLessThanOrEqual(width);
  expect(metrics.card.right).toBeLessThanOrEqual(width);
  if(width<=780){
   expect(metrics.tabRects[0].top).toBeCloseTo(metrics.tabRects[1].top,0);
   expect(Math.abs(metrics.tabRects[0].right-metrics.tabRects[0].left-(metrics.tabRects[1].right-metrics.tabRects[1].left))).toBeLessThan(2);
   expect(metrics.tabRects[0].height).toBeGreaterThanOrEqual(44);
   expect(metrics.tabRects[1].height).toBeGreaterThanOrEqual(44);
   expect(metrics.tabRects[2].height).toBeGreaterThanOrEqual(44);
   expect(metrics.tabRects[2].top).toBeCloseTo(metrics.tabRects[0].top,0);
   expect(metrics.feature.top).toBeGreaterThan(metrics.overview.top);
  }
  await page.goto('/lectures/affirmation-20261101.html');
  const reading=await page.evaluate(()=>{
   const box=document.querySelector('.compact-lecture').getBoundingClientRect();
   const h2=parseFloat(getComputedStyle(document.querySelector('#lecture-overview>h2')).fontSize);
   const h3=parseFloat(getComputedStyle(document.querySelector('#lecture-overview .summary-tier:not(details)>h3')).fontSize);
   const li=parseFloat(getComputedStyle(document.querySelector('#lecture-overview li')).fontSize);
   return {width:box.width,left:box.left,right:box.right,h2,h3,li,overflow:document.documentElement.scrollWidth-innerWidth};
  });
  expect(reading.width).toBeLessThanOrEqual(width<=780 ? width-24 : 721);
  expect(reading.left).toBeGreaterThanOrEqual(width<=780 ? 12 : -1);
  expect(reading.right).toBeLessThanOrEqual(width<=780 ? width-12 : width+1);
  expect(reading.h2).toBeGreaterThan(reading.h3);
  expect(reading.h3).toBeGreaterThanOrEqual(reading.li);
  expect(reading.overflow).toBeLessThanOrEqual(1);
  await context.close();
 }
});
