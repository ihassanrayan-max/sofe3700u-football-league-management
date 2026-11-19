const $ = id => document.getElementById(id);
const cfg = JSON.parse($('config').textContent);
const title = s => s.replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase());
const say = text => $('feedback').textContent=text;
const el = (tag,text) => {const e=document.createElement(tag);if(text!=null)e.textContent=text;return e;};
const clubs={'Arsenal':['ARS','#bd363b'],'Chelsea':['CHE','#3456a0'],'Liverpool':['LIV','#bd4038'],'Manchester City':['MCI','#447e99'],'Manchester United':['MUN','#98392f'],'Tottenham Hotspur':['TOT','#39475d']};
function club(name){const wrap=el('span');wrap.className='club';const crest=el('span',clubs[name]?.[0]||String(name).slice(0,3).toUpperCase());crest.className='crest';crest.style.setProperty('--club',clubs[name]?.[1]||'#516956');crest.setAttribute('aria-hidden','true');wrap.append(crest,el('span',name));return wrap;}
async function api(path,method='GET',data){
  let response;try{response=await fetch(path,{method,headers:{'Content-Type':'application/json','X-CSRF-Token':cfg.csrf},body:data===undefined?undefined:JSON.stringify(data)});}catch{throw Error('Connection unavailable. Check your connection and try again.');}
  const result=await response.json();
  if(!response.ok){if(response.status===401&&location.pathname!='/login'){location.assign('/login');}throw Error(result.error || 'Request failed.');}
  return result;
}
function run(fn){let busy=false;return async event=>{event?.preventDefault();if(busy)return;busy=true;const button=event?.currentTarget?.tagName==='BUTTON'?event.currentTarget:event?.currentTarget?.querySelector('button[type="submit"], button:not([type])');if(button)button.disabled=true;try{say('');await fn(event);}catch(e){say(e.message);}finally{busy=false;if(button)button.disabled=false;}};}
function grid(target,cols,rows,actions){
  const wrap=el('div');wrap.className='scroll';wrap.tabIndex=0;wrap.setAttribute('role','region');wrap.setAttribute('aria-label','Scrollable data table');const table=el('table'),head=table.createTHead().insertRow();
  const body=table.createTBody();let sorted=[...rows];
  function render(){body.replaceChildren();for(const row of sorted){const tr=body.insertRow();for(const col of cols){const cell=tr.insertCell();if(['team_name','home_team','away_team'].includes(col))cell.append(club(row[col]));else cell.textContent=col==='is_synthetic'?(row[col]?'Fictional':'Provider'):row[col]??'—';}if(actions)actions(tr.insertCell(),row);}}
  for(const col of cols){const th=el('th');th.scope='col';th.setAttribute('aria-sort','none');const short={league_position:'#',team_name:'Club',played:'P',wins:'W',draws:'D',losses:'L',goal_difference:'GD',points:'Pts'};const sort=el('button',target==='standings'?(short[col]||title(col)):title(col));sort.className='sort-button';sort.title='Sort by '+title(col);let ascending=true;sort.onclick=()=>{for(const other of head.cells)other.setAttribute('aria-sort','none');th.setAttribute('aria-sort',ascending?'ascending':'descending');sorted.sort((a,b)=>{const x=a[col],y=b[col];const cmp=x==null?-1:y==null?1:typeof x==='number'&&typeof y==='number'?x-y:String(x).localeCompare(String(y),undefined,{numeric:true});return ascending?cmp:-cmp;});ascending=!ascending;render();};th.append(sort);head.append(th);}
  if(actions)head.append(el('th','Actions'));render();wrap.append(table);$(target).replaceChildren(wrap);if(!rows.length){const empty=el('div','No matching records. Try another filter or add a record.');empty.className='empty';$(target).append(empty);}if(target==='grid'&&$('record-count'))$('record-count').textContent=rows.length+' records · Select a column heading to sort';
}
if($('login'))$('login').onsubmit=run(async()=>{await api('/api/login','POST',Object.fromEntries(new FormData($('login'))));location.assign('/');});
if($('logout'))$('logout').onclick=run(async()=>{await api('/api/logout','POST',{});location.assign('/login');});
if($('report')){
  const requested=new URLSearchParams(location.search).get('view');if([...$('report').options].some(o=>o.value===requested))$('report').value=requested;
  let requestNumber=0;
  async function report(reset){
    const current=++requestNumber;if(reset){$('field').replaceChildren(new Option('All fields',''));$('search').value='';}
    for(const fmt of ['csv','pdf'])if($(fmt)){$(fmt).removeAttribute('href');$(fmt).setAttribute('aria-disabled','true');}
    const name=$('report').value;const params=new URLSearchParams({q:$('search').value,field:$('field').value});const url='/api/reports/'+name+'?'+params;
    $('grid').replaceChildren(el('p','Loading report…'));
    try{const {rows,columns}=await api(url);if(current!==requestNumber)return;grid('grid',columns,rows);$('report-title').textContent=title(name.slice(2));
      if(reset)for(const c of columns)$('field').add(new Option(title(c),c));
      for(const fmt of ['csv','pdf'])if($(fmt)){$(fmt).href=url+'&format='+fmt;$(fmt).removeAttribute('aria-disabled');}
    }catch(e){if(current===requestNumber){$('grid').replaceChildren(el('p','Report unavailable. Apply the filter to retry.'));throw e;}}
  }
  $('report').onchange=run(()=>report(true));$('report-filter').onsubmit=run(()=>report(false));$('reset-filter').onclick=run(()=>report(true));run(()=>report(true))();
}
if($('entity')){
  let selected=null;
  function form(row){
    const t=$('entity').value;selected=row?cfg.keys[t].map(k=>row[k]).join(','):null;
    $('inputs').replaceChildren();$('save').textContent=row?'Save changes':'Create record';$('editor-title').textContent=row?'Editing '+title(t)+' · '+selected:'New '+title(t)+' record';
    for(const k of [...cfg.fields[t],...(t==='users'?['password']:[])]){
      const l=el('label',title(k)+(row&&k==='password'?' (optional)':''));let input;
      if(cfg.options[k]){input=el('select');for(const v of cfg.options[k])input.add(new Option(v,v));}
      else{input=el('input');input.type=k==='email'?'email':k==='password'?'password':k==='kickoff_at'?'datetime-local':k.endsWith('_date')?'date':k.endsWith('_id')||['goals','assists','minutes_played','home_score','away_score'].includes(k)?'number':'text';
        if(input.type==='number'){input.min=k.endsWith('_id')||k==='minutes_played'?1:0;input.max=k.endsWith('_id')?2147483647:k==='minutes_played'?120:['goals','assists'].includes(k)?20:255;input.step=1;}if(k==='password'){input.minLength=10;input.maxLength=256;input.autocomplete='new-password';}if(k==='kickoff_at')input.step=1;}
      input.name=k;input.required=!['home_score','away_score'].includes(k)&&!(row&&k==='password');
      if(row&&row[k]!=null)input.value=row[k];if(row&&cfg.keys[t].length===1&&cfg.keys[t].includes(k))input.readOnly=true;
      l.append(input);$('inputs').append(l);
    }
  }
  async function refresh(){
    const t=$('entity').value;form(null);$('grid').replaceChildren(el('p','Loading records…'));const rows=await api('/api/records/'+t);if($('entity').value!==t)return;
    grid('grid',Object.keys(rows[0]||Object.fromEntries(cfg.fields[t].map(k=>[k,null]))),rows,(td,row)=>{
      const edit=el('button','Edit'),del=el('button','Delete');td.append(edit,' ',del);edit.onclick=()=>{form(row);$('editor').scrollIntoView({block:'start'});$('inputs').querySelector('input:not([readonly]),select')?.focus({preventScroll:true});};
      del.onclick=run(async()=>{const key=cfg.keys[t].map(k=>row[k]).join(',');if(!confirm('Permanently delete '+t+' record '+key+'? This cannot be undone.'))return;await api('/api/records/'+t+'/'+key,'DELETE');await refresh();say('Record deleted.');});
    });
  }
  $('clear').onclick=()=>form(null);$('entity').onchange=run(refresh);
  $('editor').onsubmit=run(async()=>{const t=$('entity').value;$('entity').disabled=true;try{await api('/api/records/'+t+(selected?'/'+selected:''),selected?'PUT':'POST',Object.fromEntries(new FormData($('editor'))));await refresh();say('Record saved.');}finally{$('entity').disabled=false;}});
  run(refresh)();
}
if($('preview')){
  async function history(){const rows=await api('/api/import/history');grid('history',Object.keys(rows[0]||{external_id:0,match_id:0}),rows);}
  $('preview').onclick=run(async()=>{$('commit').disabled=true;const d=await api('/api/import/preview','POST',{});grid('grid',Object.keys(d.rows[0]||{}),d.rows);$('commit').disabled=!d.rows.length;say(d.rows.length+' eligible fixtures. '+d.skipped+' incomplete or unsupported records skipped.');});
  $('commit').onclick=async()=>{$('commit').disabled=true;$('preview').disabled=true;try{const d=await api('/api/import/save','POST',{});await history();say('Saved '+d.saved+' fixtures. Fetch a new preview to import again.');}catch(e){say(e.message+' Fetch a new preview to retry.');}finally{$('preview').disabled=false;}};run(history)();
}
if(location.pathname==='/'){
  let results=[],fixtures=[],matchMode='results';
  function drawMatches(){const query=$('match-search').value.trim().toLowerCase();const rows=(matchMode==='results'?results:fixtures).filter(r=>(r.home_team+' '+r.away_team).toLowerCase().includes(query)).sort((a,b)=>matchMode==='results'?b.kickoff_at.localeCompare(a.kickoff_at):a.kickoff_at.localeCompare(b.kickoff_at));$('match-count').textContent=rows.length+' '+(matchMode==='results'?'completed matches':'scheduled fixtures');$('matches').replaceChildren();
    for(const r of rows){const card=el('article');card.className='match-card';const meta=el('div');meta.className='match-meta';const date=new Date(r.kickoff_at.replace(' ','T')+'Z');meta.append(el('span',Number.isNaN(date.getTime())?r.kickoff_at:date.toLocaleString('en-GB',{day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',timeZone:'UTC'})+' UTC'),el('span',matchMode==='results'?'FULL TIME':'SCHEDULED'));card.append(meta);for(const side of ['home','away']){const line=el('div');line.className='match-team';line.append(club(r[side+'_team']),el('b',r[side+'_score']??'–'));card.append(line);}const source=el('span',r.is_synthetic?'Fictional fixture':'Provider fixture');source.className='source';card.append(source);$('matches').append(card);}
    if(!rows.length){const empty=el('div','No matches found for this selection.');empty.className='empty';$('matches').append(empty);}
  }
  for(const mode of ['results','fixtures'])$(mode+'-tab').onclick=()=>{matchMode=mode;for(const m of ['results','fixtures'])$(m+'-tab').setAttribute('aria-pressed',String(m===mode));drawMatches();};$('match-search').oninput=drawMatches;
  run(async()=>{try{const data=await Promise.all([api('/api/reports/v_match_results'),api('/api/reports/v_scheduled_fixtures')]);results=data[0].rows;fixtures=data[1].rows;drawMatches();}catch(e){$('match-count').textContent='Matches unavailable';throw e;}})();
  if($('chart')){
    run(async()=>{try{const s=await api('/api/reports/v_league_standings');let chart;
      const seasons=new Map(s.rows.map(r=>[String(r.season_id),r.season_label+' · Season '+r.season_id]));for(const [id,label] of seasons)$('season').add(new Option(label,id));
      function drawSeason(){const rows=s.rows.filter(r=>String(r.season_id)===$('season').value);grid('standings',['league_position','team_name','played','wins','draws','losses','goal_difference','points'],rows);$('metrics').replaceChildren();const played=rows.reduce((a,r)=>a+r.played,0)/2,goals=rows.reduce((a,r)=>a+r.goals_for,0);for(const [label,value,note] of [['Clubs in contention',rows.length,'Enrolled this season'],['Matches played',played,'Completed fixtures'],['Goals scored',goals,'Across both ends'],['Goals per match',played?(goals/played).toFixed(2):'—','Completed fixtures only']]){const tile=el('div');tile.className='metric';tile.append(el('span',label),el('strong',value),el('small',note));$('metrics').append(tile);}chart?.destroy();if(typeof Chart!=='undefined')chart=new Chart($('chart'),{type:'bar',data:{labels:rows.map(r=>clubs[r.team_name]?.[0]||r.team_name),datasets:[{label:'Points',data:rows.map(r=>r.points),backgroundColor:rows.map((r,i)=>i===0?'#a8c960':'#23533f'),borderRadius:3,maxBarThickness:36}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,ticks:{precision:0},grid:{color:'#edf0eb'}},x:{grid:{display:false}}}}});}
      $('season').onchange=drawSeason;drawSeason();
    }catch(e){$('metrics').replaceChildren(el('span','Season statistics unavailable.'));$('standings').replaceChildren(el('p','Standings could not be loaded. Reload to retry.'));throw e;}})();
    run(async()=>{try{const p=await api('/api/reports/v_player_totals');$('leaders').replaceChildren();for(const [i,r] of p.rows.slice(0,5).entries()){const line=el('div');line.className='leader';const player=el('div');player.className='player';player.append(el('strong',r.full_name),el('small',r.team_name+' · '+r.position));line.append(el('span',String(i+1).padStart(2,'0')),player,el('b',r.recorded_goals));$('leaders').append(line);}if(!p.rows.length)$('leaders').append(el('p','No recorded players yet.'));}catch(e){$('leaders').replaceChildren(el('p','Player totals unavailable. Reload to retry.'));throw e;}})();
  }
}
