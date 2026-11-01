// Shared clipboard handler regression: execute real site.js against a minimal DOM fixture.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');

function setup(clipboard) {
  const timers=[];
  const source={textContent:'■ 핵심 세션\n0:00 영상 시작\n1:02 강의 요약'};
  const status={textContent:''};
  const selection={selected:null,removeAllRanges(){},addRange(range){this.selected=range.target}};
  const button={
    textContent:'댓글용 타임라인 복사',
    dataset:{copyTarget:'comment'},
    parentElement:{querySelector:()=>status},
    addEventListener(_type,handler){this.click=handler}
  };
  const document={
    querySelector:()=>null,
    querySelectorAll:selector=>selector==='[data-copy-target]'?[button]:[],
    getElementById:id=>id==='comment'?source:id==='status'?status:null,
    documentElement:{style:{setProperty(){}}},
    createRange:()=>({target:null,selectNodeContents(target){this.target=target}})
  };
  const window={
    matchMedia:()=>({matches:false}),
    addEventListener(){},
    getSelection:()=>selection
  };
  vm.runInNewContext(fs.readFileSync('assets/site.js','utf8'),{
    document,window,location:{hash:''},navigator:{clipboard},
    setTimeout:(fn,ms)=>{timers.push({fn,ms});return timers.length},
    clearTimeout:()=>{}
  });
  return {source,status,button,timers,selection};
}

test('successful copy copies exact comment text and clears feedback',async()=>{
  let copied='';
  const x=setup({writeText:async text=>{copied=text}});
  await x.button.click();
  assert.equal(copied,x.source.textContent);
  assert.equal(x.button.textContent,'복사 완료 ✓');
  assert.equal(x.status.textContent,'복사됨');
  assert.equal(x.timers[0].ms,2200);
  x.timers[0].fn();
  assert.equal(x.button.textContent,'댓글용 타임라인 복사');
  assert.equal(x.status.textContent,'');
});
test('clipboard errors select original text and provide manual fallback',async()=>{
  const x=setup({writeText:async()=>{throw new Error('not allowed')}});
  await x.button.click();
  assert.equal(x.selection.selected,x.source);
  assert.equal(x.button.textContent,'텍스트 선택됨');
  assert.match(x.status.textContent,/직접 복사/);
  x.timers[0].fn();
  assert.equal(x.status.textContent,'');
});
test('missing clipboard API also supports manual selection',async()=>{
  const x=setup(undefined);
  await x.button.click();
  assert.equal(x.selection.selected,x.source);
});
