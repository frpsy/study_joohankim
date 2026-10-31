const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
class Element {
  constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.events={};this.classList={add(){}};this.value='';}
  setAttribute(k,v){this[k]=v;}
  append(...nodes){this.children.push(...nodes);}
  replaceChildren(...nodes){this.children=nodes;}
  addEventListener(k,fn){this.events[k]=fn;}
  querySelectorAll(selector){return this.children.flatMap(n=>typeof n==='object'?[...(selector==='label.study-check'&&n.tag==='label'&&n.className==='study-check'?[n]:selector==='.actions'&&n.className==='actions'?[n]:[]),...n.querySelectorAll(selector)]:[]);}
  querySelector(s){return this.querySelectorAll(s)[0];}
  all(){return [this,...this.children.flatMap(n=>typeof n==='object'?n.all():[])];}
}
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const empty={exists:()=>false};
async function setup(getDoc=async()=>empty){
 const root=new Element('root');root.dataset.lecture='test-video';
 let auth;let fail=false;let commits=0;const saved=[];
 const sdk={doc:(...args)=>args,collection:(...args)=>args,getDoc,serverTimestamp:()=>123,
  writeBatch:()=>{const writes=[];return {set:(...args)=>writes.push(args),commit:async()=>{commits++;if(fail)throw Error('offline');saved.push(...writes);}};}};
 const context={document:{getElementById:()=>root,createElement:t=>new Element(t),createTextNode:t=>t},getDb:async()=>({db:{},fs:sdk}),onUserChange:cb=>{auth=cb;}};
 const source=fs.readFileSync('assets/progress.js','utf8').replace(/^import .*;\n/m,'');
 vm.runInNewContext(source,context);await tick();
 return {root,auth:u=>auth(u),find:text=>root.all().find(n=>n.textContent===text),fail:v=>fail=v,saved,commits:()=>commits};
}
test('failed reads expose retry only; successful retry restores stored memo',async()=>{
 let failed=true;const x=await setup(async()=>{if(failed)throw Error('read');return {exists:()=>true,data:()=>({text:'existing memo'})};});
 x.auth({uid:'a'});await tick();assert.equal(x.find('저장'),undefined);assert.ok(x.find('다시 불러오기'));
 failed=false;x.find('다시 불러오기').events.click();await tick();assert.ok(x.find('저장'));assert.equal(x.root.all().find(n=>n.tag==='textarea').value,'existing memo');
});
test('late read cannot restore signed-out or previous-account form',async()=>{
 const pending=[];const x=await setup(()=>new Promise(resolve=>pending.push(resolve)));
 x.auth({uid:'a'});x.auth(null);pending.splice(0).forEach(r=>r({exists:()=>true,data:()=>({text:'private a'})}));await tick();assert.equal(x.find('저장'),undefined);
 x.auth({uid:'a'});const old=pending.splice(0);x.auth({uid:'b'});pending.splice(0).forEach(r=>r({exists:()=>true,data:()=>({text:'private b'})}));await tick();old.forEach(r=>r({exists:()=>true,data:()=>({text:'private a'})}));await tick();assert.equal(x.root.all().find(n=>n.tag==='textarea').value,'private b');
});
test('progress, note and history commit together; failure can be retried',async()=>{
 const x=await setup();x.auth({uid:'a'});await tick();x.root.all().find(n=>n.tag==='textarea').value='memo';x.root.all().find(n=>n.id==='sp-study').checked=true;
 x.fail(true);await x.find('저장').events.click();assert.equal(x.saved.length,0);assert.equal(x.commits(),1);assert.equal(x.find('저장').disabled,false);
 x.fail(false);await x.find('저장').events.click();assert.equal(x.commits(),2);assert.equal(x.saved.length,4); // progress, note, study history, note history
});
test('late commit status cannot replace signed-out status',async()=>{
 const x=await setup();x.auth({uid:'a'});await tick();const saving=x.find('저장').events.click();x.auth(null);await saving;assert.equal(x.find('저장했습니다.'),undefined);assert.equal(x.find('저장'),undefined);
});
test('home ignores a previous account badge response after logout',async()=>{
 const nodes=Object.fromEntries(['settings-toggle','settings','account-state','account-action','account-history'].map(id=>[id,new Element('div')]));
 let auth,resolve,rendered=0;
 const context={document:{getElementById:id=>nodes[id],querySelectorAll:()=>[]},location:{hash:''},window:{addEventListener(){}},getDb:async()=>({db:{},fs:{collection(){},getDocs:()=>new Promise(r=>resolve=r)}}),onUserChange:cb=>{auth=cb;},signInWithGoogle(){},signOutUser(){}};
 vm.runInNewContext(fs.readFileSync('assets/account.js','utf8').replace(/^import .*;\n/m,''),context);
 auth({uid:'a',displayName:'A'});await tick();auth(null);resolve({forEach(){rendered++;}});await tick();assert.equal(rendered,0);assert.equal(nodes['account-action'].textContent,'구글로 로그인');
});
test('history ignores a previous account response after logout',async()=>{
 const nodes={'history-status':new Element('div'),'history-items':new Element('ol')};nodes['history-status'].after=()=>{};
 let auth,resolve;
 const context={document:{getElementById:id=>nodes[id],createElement:t=>new Element(t)},fetch:async()=>({json:async()=>[]}),getDb:async()=>({db:{},fs:{collection(){},query(){},orderBy(){},limit(){},getDocs:()=>new Promise(r=>resolve=r)}}),onUserChange:cb=>{auth=cb;}};
 const html=fs.readFileSync('study-history.html','utf8');const source=html.match(/<script type="module">([\s\S]*?)<\/script>/)[1].replace(/^import .*;\n/m,'');
 vm.runInNewContext(source,context);auth({uid:'a'});await tick();auth(null);resolve({empty:false,docs:[{data:()=>({lectureId:'a',kind:'note',value:true})}],size:1});await tick();assert.equal(nodes['history-items'].children.length,0);assert.match(nodes['history-status'].textContent,/로그인/);
});
