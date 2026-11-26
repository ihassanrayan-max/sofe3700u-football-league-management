// Run with node --test tests/scheduled_fixtures_ui.test.js. No browser or network.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
class Element {
  get cells(){return this.children;}
  constructor(){this.children=[];this.style={setProperty(){}};this.dataset={};this.textContent='';}
  append(...children){this.children.push(...children);}
  replaceChildren(...children){this.children=children;}
  setAttribute(){}
  createTHead(){const e=new Element();this.append(e);return e;}
  createTBody(){return this.createTHead();}
  insertRow(){return this.createTHead();}
  insertCell(){return this.createTHead();}
}
const elements={config:{textContent:'{}'}};
const context=vm.createContext({location:{pathname:'/offline-test'},document:{getElementById:id=>elements[id]||null,createElement:()=>new Element()}});
vm.runInContext(fs.readFileSync(path.join(__dirname,'../static/ui.js'),'utf8'),context);
test('empty scheduled table explains completed season without fabricated rows',()=>{
  elements.grid=new Element();
  context.grid('grid',['match_id','kickoff_at','season_label','match_status'],[],null,context.scheduledEmptyMessage(true,''));
  const empty=elements.grid.children[1];
  assert.match(empty.textContent,/No scheduled fixtures are available for the selected season and clubs/);
  assert.match(empty.textContent,/2023\/24 is a completed season/);
  const table=elements.grid.children[0].children[0];
  assert.equal(table.children[1].children.length,0);
});
test('search miss does not claim the entire scope is empty',()=>{
  const message=context.scheduledEmptyMessage(true,'Arsenal');
  assert.match(message,/match the current search/);
  assert.doesNotMatch(message,/completed season/);
});
test('scheduled rendering keeps actual status season and fictional label',()=>{
  elements.grid=new Element();
  context.grid('grid',['match_status','season_label','is_synthetic'],[
    {match_status:'SCHEDULED',season_label:'2025/26',is_synthetic:1}
  ],null,context.scheduledEmptyMessage(false,''));
  const cells=elements.grid.children[0].children[0].children[1].children[0].children;
  assert.deepEqual(cells.map(c=>c.textContent),['SCHEDULED','2025/26','Fictional']);
  assert.match(context.scheduledEmptyMessage(false,''),/not real upcoming matches/);
});

test('scheduled pagination retains all rows and exports are separate from page slicing',()=>{
  elements.grid=new Element();
  const rows=Array.from({length:12},(_,i)=>({match_id:i+1}));
  context.grid('grid',['match_id'],rows,null,'',10);
  const table=elements.grid.children[0].children[0];
  const pager=elements.grid.children[1];
  assert.equal(table.children[1].children.length,10);
  pager.children[2].onclick();
  assert.equal(table.children[1].children.length,2);
  assert.equal(table.children[1].children[0].children[0].textContent,11);
  pager.children[0].onclick();
  assert.equal(table.children[1].children[0].children[0].textContent,1);
  assert.equal(rows.length,12);
  const sort=table.children[0].children[0].children[0].children[0];
  sort.onclick();sort.onclick();
  assert.equal(table.children[1].children[0].children[0].textContent,12);
  assert.match(pager.children[1].textContent,/Page 1 of 2/);
});
test('source selector requests demo explicitly and preserves it in export links',async()=>{
  const controls={};
  for(const name of ['config','report','field','search','csv','pdf','grid','report-title','report-filter','reset-filter','feedback','fixture-source','fixture-source-control','fixture-source-note']){
    controls[name]=new Element();
    controls[name].removeAttribute=()=>{};
    controls[name].add=()=>{};
  }
  controls.config.textContent='{"api_football":true}';
  controls.report.value='v_scheduled_fixtures';
  controls.report.options=[{value:'v_scheduled_fixtures'}];
  controls.search.value='';controls.field.value='';
  const calls=[];
  const sandbox=vm.createContext({location:{pathname:'/reports',search:''},URLSearchParams,
    Option:function(text,value){this.text=text;this.value=value;},
    document:{getElementById:id=>controls[id]||null,createElement:()=>new Element()},
    fetch:async url=>{calls.push(url);return {ok:true,status:200,json:async()=>({columns:['match_id','match_status'],rows:[]})};}});
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../static/ui.js'),'utf8'),sandbox);
  await new Promise(resolve=>setImmediate(resolve));
  assert.ok(!calls[0].includes('phase2-demo'));
  controls['fixture-source'].value='phase2-demo';
  await controls['fixture-source'].onchange();
  assert.match(calls.at(-1),/source=phase2-demo/);
  assert.match(controls.csv.href,/source=phase2-demo.*format=csv/);
  assert.match(controls.pdf.href,/source=phase2-demo.*format=pdf/);
  assert.match(controls['fixture-source-note'].textContent,/fictional records/);
  controls.report.value='v_player_totals';controls.report.onchange();
  await new Promise(resolve=>setImmediate(resolve));
  assert.ok(!calls.at(-1).includes('phase2-demo'));
});
