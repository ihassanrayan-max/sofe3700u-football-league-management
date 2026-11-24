// Run with node --test tests/player_totals_ui.test.js. No browser or network.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
class Element {
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
test('actual table renderer preserves zero, unknown and independent coverage',()=>{
  elements.grid=new Element();
  context.grid('grid',['recorded_goals','recorded_assists'],[
    {recorded_goals:0,recorded_assists:null,known_goal_appearances:1,unknown_goal_appearances:1,known_assist_appearances:0,unknown_assist_appearances:2}
  ]);
  const table=elements.grid.children[0].children[0];
  const cells=table.children[1].children[0].children;
  assert.equal(cells[0].textContent,0);
  assert.equal(cells[1].textContent,'—');
  assert.match(cells[0].children[0].textContent,/Partial observed coverage: 1 known, 1 unknown/);
  assert.match(cells[1].children[0].textContent,/0 known, 2 unknown/);
});
test('leaders include partial and zero subtotals; exclude unknown and rank numerically',()=>{
  const rows=[{player_id:1,recorded_goals:null},{player_id:2,recorded_goals:0},
    {player_id:3,recorded_goals:3,known_goal_appearances:2,unknown_goal_appearances:1},
    {player_id:4,recorded_goals:2}];
  assert.deepEqual(Array.from(context.knownGoalLeaders(rows),r=>r.player_id),[3,4,2]);
  assert.match(context.statCoverage(rows[2],'goal'),/Partial observed coverage/);
  assert.equal(context.statCoverage({known_goal_appearances:2,unknown_goal_appearances:0},'goal'),'Complete observed coverage: 2 known, 0 unknown appearances');
});
