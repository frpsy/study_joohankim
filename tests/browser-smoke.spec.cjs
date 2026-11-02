const {test,expect}=require('@playwright/test');
const studyVersion=require('../build-info.json').version;
const studyLectures=require('../lectures.json');
const studyMaterials=require('../materials.json');
const expectedLibraryCount=studyLectures.length+studyMaterials.length;
const kimLectureCount=studyLectures.filter(x=>x.creator==='김주환').length;
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
    const disclosure=page.locator('details.timeline-disclosure');
    await expect(disclosure).not.toHaveAttribute('open');
    await expect(disclosure.locator('summary')).toHaveText('전체 타임라인 보기');
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
    await disclosure.locator('summary').click();
    await expect(disclosure).not.toHaveAttribute('open');
    await expect(page.locator('#comment')).toBeHidden();
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
  for(const [url,title] of [['/concepts.html','용어와 개념'],['/study-history.html','학습 이력'],['/index.html','자료 모음']]){
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

test('footer account is unobtrusive and login/close still work',async({browser})=>{
 const context=await browser.newContext({viewport:{width:390,height:844}});
 const page=await context.newPage();
 await page.route('**/assets/firebase.js*',route=>route.fulfill({status:200,contentType:'text/javascript',body:`
    let observer;
    export const getDb=async()=>({db:{},fs:{getDocs:async()=>({forEach(){}}),collection(){}}});
    export function onUserChange(cb){observer=cb;cb(null);return Promise.resolve(()=>{});}
    export function signInWithGoogle(){
      document.documentElement.dataset.loginInvoked='yes';
      observer({uid:'mock',displayName:'테스트'});
      return Promise.resolve();
    }
    export function signOutUser(){observer(null);return Promise.resolve();}
  `}));
 await page.goto('/index.html');
 await expect(page.locator('.hub-hero h1')).toContainText('내면의 서재');
 await expect(page.locator('#settings')).toBeHidden();
 const actions=page.locator('.hub-actions > *');
 await expect(actions).toHaveCount(2);
 await expect(actions.nth(0)).toHaveText('자료 살펴보기');
 await expect(actions.nth(1)).toHaveText('미니강좌');
 await expect(page.locator('.hub-hero #settings-toggle')).toHaveCount(0);
 const entry=page.locator('.site-footer-inner #settings-toggle');
 await expect(entry).toHaveText('계정');
 await expect(entry).toBeVisible();
 expect(await entry.evaluate(el=>el.getBoundingClientRect().height)).toBeGreaterThanOrEqual(44);
 await entry.click();
 await expect(entry).toHaveAttribute('aria-expanded','true');
 await expect(page.locator('#settings')).toBeVisible();
 await expect(page.locator('#account-action')).toBeEnabled();
 const panelY=await page.locator('#settings').evaluate(el=>el.getBoundingClientRect().top + scrollY);
 const footerY=await page.locator('.site-footer').evaluate(el=>el.getBoundingClientRect().top + scrollY);
 expect(panelY).toBeGreaterThan(footerY);
 await page.locator('#account-action').click();
 await expect(page.locator('html')).toHaveAttribute('data-login-invoked','yes');
 await expect(page.locator('#account-action')).toHaveText('로그아웃');
 await page.locator('#account-action').click();
 await expect(page.locator('#account-action')).toHaveText('Google로 로그인');
 await page.locator('#account-close').click();
 await expect(page.locator('#settings')).toBeHidden();
 await context.close();
});


test('editorial library identity and reading hierarchy stay consistent',async({browser})=>{
  const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
  const page=await context.newPage();
  for(const url of ['/index.html','/concepts.html','/study-history.html','/lectures/izYj8g-j00U.html']){
    await page.goto(url);
    await expect(page.locator('.site-brand .brand-name')).toContainText('내면의 서재');
    await expect(page.locator('.brand-symbol')).toBeVisible();
    expect(await page.locator('.brand-symbol').evaluate(el=>el.naturalWidth)).toBeGreaterThan(0);
    await expect(page).toHaveTitle(/내면의 서재/);
    const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth);
    expect(overflow,'no horizontal overflow at '+url).toBeLessThanOrEqual(1);
  }
  await page.goto('/index.html');
  await expect(page.locator('.hub-hero h1')).toHaveText('내면의 서재');
  const compact=await page.evaluate(()=>{
    const header=document.querySelector('.site-header').getBoundingClientRect();
    const title=document.querySelector('.hub-hero h1').getBoundingClientRect();
    const cards=[...document.querySelectorAll('.lecture')];
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
  await expect(page.locator('#lecture-list .lecture:visible')).toHaveCount(1);
  await context.close();
});

test('desktop home presents a side-by-side editorial hero and readable cards',async({browser})=>{
  const context=await browser.newContext({viewport:{width:1280,height:800},reducedMotion:'reduce'});
  const page=await context.newPage();
  await page.goto('/index.html');
  const hero=await page.evaluate(()=>{
    const title=document.querySelector('.hub-hero .page-hero').getBoundingClientRect();
    const featured=document.querySelector('.latest-entry').getBoundingClientRect();
    const card=document.querySelector('.lecture').getBoundingClientRect();
    return {heroSideBySide:featured.left>title.right-12,cardWidth:card.width};
  });
  expect(hero.heroSideBySide).toBe(true);
  expect(hero.cardWidth).toBeGreaterThan(350);
  await context.close();
});

test('catalog searches by creator without losing video ID progress hooks',async({page})=>{
  await page.goto('/index.html');
  const items=page.locator('#lecture-list .lecture');
  await expect(items).toHaveCount(expectedLibraryCount);
  await expect(page.locator('[data-creator="Andrew Huberman"]')).toHaveCount(1);
  await page.locator('#search').fill('Huberman');
  await expect(page.locator('#count')).toHaveText('1개 자료');
  await expect(page.locator('#lecture-list .lecture:visible')).toHaveCount(1);
  await expect(page.locator('#lecture-list .lecture:visible')).toHaveAttribute('data-video-id','QmOF0crdyRU');
  await page.locator('#search').fill('김주환');
  await expect(page.locator('#count')).toHaveText(kimLectureCount+'개 자료');
});

test('catalog restores a shared search and returns to it after reading',async({page})=>{
  await page.goto('/index.html?q=Huberman&source=test#lectures');
  await expect(page.locator('#search')).toHaveValue('Huberman');
  await expect(page.locator('#lecture-list .lecture:visible')).toHaveCount(1);
  await page.locator('#lecture-list .lecture:visible').click();
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

for(const width of [360,1280]){
 test('study status is saved directly with two plain buttons at '+width+'px',async({browser})=>{
  const context=await browser.newContext({viewport:{width,height:844}});
  const page=await context.newPage();
  // A deterministic SDK fixture exercises the UI without using a real account.
  await page.route('**/assets/firebase.js?*',route=>route.fulfill({contentType:'text/javascript',body:`
   export function onUserChange(cb){cb({uid:'test-user'})}
   export async function getDb(){return {db:{},fs:{
    doc:(...args)=>args,collection:(...args)=>args,serverTimestamp:()=>1,
    getDoc:async()=>({exists:()=>true,data:()=>({study:true,review:false})}),
    writeBatch:()=>({set(){},commit:()=>new Promise(resolve=>setTimeout(resolve,100))})
   }}}
  `}));
  await page.goto('/lectures/izYj8g-j00U.html');
  const widget=page.locator('#study-progress');
  await expect(widget.locator('details,summary,input')).toHaveCount(0);
  await expect(widget.getByRole('button')).toHaveCount(2);
  await expect(widget.getByRole('button',{name:'학습 완료 취소',exact:true})).toHaveText('학습 완료 ✓');
  const review=widget.getByRole('button',{name:'복습 완료',exact:true});
  await expect(review).toBeVisible();
  expect(await review.evaluate(el=>el.getBoundingClientRect().height)).toBeGreaterThanOrEqual(44);
  await review.click();
  await expect(widget.getByRole('status')).toHaveText('복습 완료 저장됨');
  await expect(widget.getByRole('button',{name:'복습 완료 취소',exact:true})).toHaveText('복습 완료 ✓');
  await widget.getByRole('button',{name:'학습 완료 취소',exact:true}).click();
  await expect(widget.getByRole('button',{name:'학습 완료',exact:true})).toHaveText('학습 완료');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth-window.innerWidth)).toBeLessThanOrEqual(1);
  await context.close();
 });
}
