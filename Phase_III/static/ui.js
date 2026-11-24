const $ = id => document.getElementById(id);
const cfg = JSON.parse($('config').textContent);
const title = s => s.replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase());
const say = text => $('feedback').textContent=text;
const el = (tag,text) => {const e=document.createElement(tag);if(text!=null)e.textContent=text;return e;};
const clubs={'Arsenal':['ARS','#bd363b'],'Chelsea':['CHE','#3456a0'],'Liverpool':['LIV','#bd4038'],'Manchester City':['MCI','#447e99'],'Manchester United':['MUN','#98392f'],'Tottenham Hotspur':['TOT','#39475d']};
function club(name){const wrap=el('span');wrap.className='club';const crest=el('span',clubs[name]?.[0]||String(name).slice(0,3).toUpperCase());crest.className='crest';crest.style.setProperty('--club',clubs[name]?.[1]||'#516956');crest.setAttribute('aria-hidden','true');wrap.append(crest,el('span',name));return wrap;}
async function api(path,method='GET',data){
  let response;try{response=await fetch(path,{method,headers:{'Content-Type':'application/json','X-CSRF-Token':cfg.csrf},body:data===undefined?undefined:JSON.stringify(data)});}catch{throw Error('Connection unavailable. Check your connection and try again.');}
  let result;try{result=await response.json();}catch{throw Error('The server returned an unreadable response. Please reload and try again.');}
  if(!response.ok){if(response.status===401&&location.pathname!='/login'){location.assign('/login');}throw Error(result.error || 'Request failed.');}
  return result;
}
function run(fn){let busy=false;return async event=>{event?.preventDefault();if(busy)return;busy=true;const button=event?.currentTarget?.tagName==='BUTTON'?event.currentTarget:event?.currentTarget?.querySelector('button[type="submit"], button:not([type])');if(button)button.disabled=true;try{say('');await fn(event);}catch(e){say(e.message);}finally{busy=false;if(button)button.disabled=false;}};}
function statCoverage(row,stat){
  const known=row['known_'+stat+'_appearances'],unknown=row['unknown_'+stat+'_appearances'];
  if(known==null||unknown==null)return '';
  return (unknown>0?'Partial observed coverage':'Complete observed coverage')+': '+known+' known, '+unknown+' unknown appearances';
}
function knownGoalLeaders(rows){
  return rows.filter(row=>row.recorded_goals!=null).sort((a,b)=>b.recorded_goals-a.recorded_goals||a.player_id-b.player_id).slice(0,5);
}
function renderStat(cell,row,col){
  cell.textContent=row[col]??'—';
  const stat={recorded_goals:'goal',recorded_assists:'assist'}[col];
  const coverage=stat&&statCoverage(row,stat);
  if(coverage){const note=el('small',coverage);note.className='stat-coverage';cell.append(note);}
}
function grid(target,cols,rows,actions){
  const wrap=el('div');wrap.className='scroll';wrap.tabIndex=0;wrap.setAttribute('role','region');wrap.setAttribute('aria-label','Scrollable data table');const table=el('table'),head=table.createTHead().insertRow();
  const body=table.createTBody();let sorted=[...rows];
  function render(){body.replaceChildren();for(const row of sorted){const tr=body.insertRow();if(target==='standings'&&Number(row.league_position)===1)tr.dataset.leader='true';for(const col of cols){const cell=tr.insertCell();if(['team_name','home_team','away_team'].includes(col))cell.append(club(row[col]));else if(col==='is_synthetic')cell.textContent=row[col]?'Fictional':'Provider';else renderStat(cell,row,col);}if(actions)actions(tr.insertCell(),row);}}
  for(const col of cols){const th=el('th');th.scope='col';th.setAttribute('aria-sort','none');const short={league_position:'#',team_name:'Club',played:'P',wins:'W',draws:'D',losses:'L',goal_difference:'GD',points:'Pts'};const sort=el('button',target==='standings'?(short[col]||title(col)):title(col));sort.className='sort-button';sort.title='Sort by '+title(col);sort.setAttribute('aria-label','Sort by '+title(col));let ascending=true;sort.onclick=()=>{for(const other of head.cells)other.setAttribute('aria-sort','none');th.setAttribute('aria-sort',ascending?'ascending':'descending');sorted.sort((a,b)=>{const x=a[col],y=b[col];const cmp=x==null&&y==null?0:x==null?-1:y==null?1:typeof x==='number'&&typeof y==='number'?x-y:String(x).localeCompare(String(y),undefined,{numeric:true});return ascending?cmp:-cmp;});ascending=!ascending;render();};th.append(sort);head.append(th);}
  if(actions)head.append(el('th','Actions'));render();wrap.append(table);$(target).replaceChildren(wrap);if(!rows.length){const empty=el('div',target==='history'?'No provider fixtures saved yet. Fetch a preview to begin.':'No matching records. Try another selection or clear the filter.');empty.className='empty';$(target).append(empty);}if(target==='grid'&&$('record-count'))$('record-count').textContent=rows.length+' records · Select a column heading to sort';
}
if($('login'))$('login').onsubmit=run(async()=>{await api('/api/login','POST',Object.fromEntries(new FormData($('login'))));location.assign('/');});
if($('logout'))$('logout').onclick=run(async()=>{await api('/api/logout','POST',{});location.assign('/login');});
if($('report')){
  const requested=new URLSearchParams(location.search).get('view');if([...$('report').options].some(o=>o.value===requested))$('report').value=requested;
  let requestNumber=0;
  async function report(reset){
    const current=++requestNumber;if(reset){$('field').replaceChildren(new Option('All fields',''));$('search').value='';}
    for(const fmt of ['csv','pdf'])if($(fmt)){$(fmt).removeAttribute('href');$(fmt).setAttribute('aria-disabled','true');}
    const name=$('report').value;if($('report-coverage'))$('report-coverage').hidden=!(cfg.api_football&&name==='v_player_totals');const params=new URLSearchParams({q:$('search').value,field:$('field').value});const url='/api/reports/'+name+'?'+params;
    $('grid').replaceChildren(el('p','Loading report…'));
    try{const {rows,columns}=await api(url);if(current!==requestNumber)return;grid('grid',columns,rows);$('report-title').textContent=title(name.slice(2));
      if(reset)for(const c of columns)$('field').add(new Option(title(c),c));
      for(const fmt of ['csv','pdf'])if($(fmt)){$(fmt).href=url+'&format='+fmt;$(fmt).removeAttribute('aria-disabled');}
    }catch(e){if(current===requestNumber){$('grid').replaceChildren(el('p','Report unavailable. Apply the filter to retry.'));throw e;}}
  }
  $('report').onchange=()=>{say('');report(true).catch(e=>say(e.message));};$('report-filter').onsubmit=run(()=>report(false));$('reset-filter').onclick=run(()=>report(true));run(()=>report(true))();
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
    const t=$('entity').value;form(null);say('');$('grid').replaceChildren(el('p','Loading records…'));let rows;try{rows=await api('/api/records/'+t);}catch(e){if($('entity').value===t)$('grid').replaceChildren(el('p','Records unavailable. Select the table again to retry.'));throw e;}if($('entity').value!==t)return;
    grid('grid',Object.keys(rows[0]||Object.fromEntries(cfg.fields[t].map(k=>[k,null]))),rows,(td,row)=>{
      const edit=el('button','Edit'),del=el('button','Delete');td.append(edit,' ',del);edit.onclick=()=>{form(row);$('editor').scrollIntoView({block:'start'});$('inputs').querySelector('input:not([readonly]),select')?.focus({preventScroll:true});};
      del.onclick=run(async()=>{const key=cfg.keys[t].map(k=>row[k]).join(',');if(!confirm('Permanently delete '+t+' record '+key+'? This cannot be undone.'))return;await api('/api/records/'+t+'/'+key,'DELETE');await refresh();say('Record deleted.');});
    });
  }
  $('clear').onclick=()=>form(null);$('entity').onchange=()=>{say('');refresh().catch(e=>say(e.message));};
  $('editor').onsubmit=run(async()=>{const t=$('entity').value;$('entity').disabled=true;try{await api('/api/records/'+t+(selected?'/'+selected:''),selected?'PUT':'POST',Object.fromEntries(new FormData($('editor'))));await refresh();say('Record saved.');}finally{$('entity').disabled=false;}});
  run(refresh)();
}
if($('preview')){
  let previewId=null,previewVersion=0;
  async function history(){try{const rows=await api('/api/import/history');grid('history',Object.keys(rows[0]||{external_id:0,match_id:0}),rows,(td,row)=>{if(!cfg.api_football)return;const button=el('button','Team statistics');td.append(button);button.onclick=run(async()=>{const version=++previewVersion;previewId=null;$('commit').disabled=true;const stats=await api('/api/import/statistics?match_id='+row.match_id);if(version!==previewVersion)return;grid('grid',['team','statistic','value'],stats);$('commit').disabled=true;say('Saved provider statistics. A dash means unknown; an empty table means coverage has not been imported or was unavailable.');});});}catch(e){$('history').replaceChildren(el('p','Saved imports unavailable. Reload to retry.'));throw e;}}
  $('preview').onclick=run(async()=>{const version=++previewVersion;previewId=null;$('commit').disabled=true;$('grid').replaceChildren(el('p','Fetching eligible provider fixtures…'));let d;try{d=await api('/api/import/preview','POST',{kind:$('import-kind')?.value||'fixtures'});}catch(e){$('grid').replaceChildren(el('p','Preview unavailable. Check the message above, then fetch again.'));throw e;}if(version!==previewVersion)return;previewId=d.preview_id;grid('grid',Object.keys(d.rows[0]||{}),d.rows);$('commit').disabled=!d.rows.length;say(d.rows.length+' eligible fixtures. '+d.skipped+' incomplete or unsupported records skipped.');});
  if($('import-kind'))$('import-kind').onchange=()=>{previewVersion++;previewId=null;$('commit').disabled=true;};
  $('commit').onclick=async()=>{$('commit').disabled=true;$('preview').disabled=true;try{const d=await api('/api/import/save','POST',cfg.api_football?{preview_id:previewId}:{});await history();say('Saved '+d.saved+' fixtures. Fetch a new preview to import again.');}catch(e){say(e.message+' Fetch a new preview to retry.');}finally{$('preview').disabled=false;}};run(history)();
}
// Dashboard projections use only successfully returned report rows.
function kickoff(value) {
  const normalized=String(value).replace(' ','T');
  const date=new Date(/Z$|[+-]\d{2}:\d{2}$/.test(normalized)?normalized:normalized+'Z');
  return Number.isNaN(date.getTime())?String(value):date.toLocaleString('en-GB',{
    day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',timeZone:'UTC'
  })+' UTC';
}
function message(target,text,error=false) {
  const node=el('div',text);node.className=error?'error-state':'empty';$(target).replaceChildren(node);
}
function origin(row) { return row.is_synthetic?'Fictional course fixture':'Provider fixture'; }
function matchLine(row,side) {
  const line=el('div');line.className='match-team';
  line.append(club(row[side+'_team']),el('b',row[side+'_score']??'–'));return line;
}
if(location.pathname==='/') {
  const matchData={results:null,fixtures:null};
  const matchErrors={results:false,fixtures:false};
  let matchMode='results';
  function drawMatches() {
    const available=matchData[matchMode];
    if(available===null) {
      $('match-count').textContent=matchErrors[matchMode]?'Matches unavailable':'Loading matches…';
      message('matches',matchErrors[matchMode]?'Could not load this match list. Reload to retry.':'Loading matches…',matchErrors[matchMode]);return;
    }
    const query=$('match-search').value.trim().toLowerCase();
    const rows=available.filter(r=>(r.home_team+' '+r.away_team).toLowerCase().includes(query));
    $('match-count').textContent=rows.length+' '+(matchMode==='results'?'completed matches':'scheduled fixtures');
    $('matches').replaceChildren();
    for(const row of rows) {
      const card=el('article');card.className='match-card';
      const meta=el('div');meta.className='match-meta';
      const status=el('span',matchMode==='results'?'FULL TIME':'SCHEDULED');status.className='match-status';
      meta.append(el('span',kickoff(row.kickoff_at)),status);
      const source=el('span',origin(row));source.className='source'+(row.is_synthetic?' fictional':'');
      card.append(meta,matchLine(row,'home'),matchLine(row,'away'),source);$('matches').append(card);
    }
    if(!rows.length)message('matches',query?'No matching clubs. Try another search.':'No '+(matchMode==='results'?'completed matches':'scheduled fixtures')+' recorded yet.');
  }
  function spotlight(mode,rows) {
    const target=mode==='results'?'featured-match':'fixture-spotlight';
    if(!rows.length){message(target,mode==='results'?'The story starts at full time. No completed matches recorded yet.':'No scheduled fixtures recorded.');return;}
    const row=rows[0];$(target).replaceChildren();
    if(mode==='results') {
      const date=el('div',kickoff(row.kickoff_at)+' · FULL TIME');date.className='featured-date';
      const scoreboard=el('div');scoreboard.className='scoreboard';
      const score=el('strong',row.home_score+' : '+row.away_score);score.className='score';
      scoreboard.append(club(row.home_team),score,club(row.away_team));
      const source=el('p',origin(row)+' · '+(cfg.api_football?'EPL '+cfg.active_season+' · six-club subset':'All recorded seasons'));source.className='featured-source';
      $(target).append(date,scoreboard,source);
    } else {
      const date=el('p',kickoff(row.kickoff_at));date.className='fixture-date';
      const source=el('span',origin(row)+' · Earliest scheduled');source.className='source';
      $(target).append(date,matchLine(row,'home'),matchLine(row,'away'),source);
    }
  }
  for(const mode of ['results','fixtures']) {
    $(mode+'-tab').onclick=()=>{
      matchMode=mode;
      for(const other of ['results','fixtures'])$(other+'-tab').setAttribute('aria-pressed',String(other===mode));
      drawMatches();
    };
    const view=mode==='results'?'v_match_results':'v_scheduled_fixtures';
    api('/api/reports/'+view).then(data=>{
      matchData[mode]=[...data.rows].sort((a,b)=>mode==='results'?b.kickoff_at.localeCompare(a.kickoff_at):a.kickoff_at.localeCompare(b.kickoff_at));
      spotlight(mode,matchData[mode]);drawMatches();
    }).catch(error=>{
      matchErrors[mode]=true;message(mode==='results'?'featured-match':'fixture-spotlight','Match data unavailable. Reload to retry.',true);
      drawMatches();say(error.message);
    });
  }
  $('match-search').oninput=drawMatches;
  if($('chart')) {
    let chart,standings=[];
    const measures={points:'Points',goals_for:'Goals scored',goal_difference:'Goal difference'};
    function drawChart(rows) {
      const measure=$('chart-measure').value;
      $('chart-summary').textContent=rows.map(row=>row.team_name+': '+row[measure]).join(' · ');
      $('chart').setAttribute('aria-label',measures[measure]+' by club. Exact values are listed below.');
      chart?.destroy();
      if(typeof Chart==='undefined')return;
      chart=new Chart($('chart'),{
        type:'bar',data:{labels:rows.map(row=>clubs[row.team_name]?.[0]||row.team_name),datasets:[{
          label:measures[measure],data:rows.map(row=>row[measure]),
          backgroundColor:rows.map((row,i)=>row[measure]<0?'#ef8583':i===0?'#c2f36b':'#46b88b'),
          borderRadius:4,maxBarThickness:32
        }]},options:{responsive:true,maintainAspectRatio:false,
          animation:matchMedia('(prefers-reduced-motion: reduce)').matches?false:{duration:350},
          plugins:{legend:{display:false},tooltip:{backgroundColor:'#24352d',titleColor:'#eff9ed',bodyColor:'#dce8dc',padding:12}},
          scales:{y:{beginAtZero:true,ticks:{precision:0,color:'#9db1a4'},grid:{color:'#2b3a33'},border:{display:false}},
            x:{ticks:{color:'#b3c6b8',font:{size:11}},grid:{display:false},border:{display:false}}}}
      });
    }
    function currentSeason(){return standings.filter(row=>String(row.season_id)===$('season').value);}
    function drawSeason() {
      const rows=currentSeason();
      grid('standings',['league_position','team_name','played','wins','draws','losses','goal_difference','points'],rows);
      $('metrics').replaceChildren();
      const played=rows.reduce((total,row)=>total+Number(row.played),0)/2;
      const goals=rows.reduce((total,row)=>total+Number(row.goals_for),0);
      for(const [label,value,note] of [
        ['Clubs in contention',rows.length,'Enrolled this season'],['Matches played',played,'Completed fixtures'],
        ['Goals scored',goals,'Across both ends'],['Goals per match',played?(goals/played).toFixed(2):'—','Completed fixtures only']
      ]) {
        const tile=el('div');tile.className='metric';tile.append(el('span',label),el('strong',value),el('small',note));$('metrics').append(tile);
      }
      drawChart(rows);
    }
    $('season').onchange=drawSeason;$('chart-measure').onchange=()=>drawChart(currentSeason());
    api('/api/reports/v_league_standings').then(data=>{
      standings=data.rows;
      for(const [id,label] of new Map(standings.map(row=>[String(row.season_id),row.season_label+' · Season '+row.season_id])))$('season').add(new Option(label,id));
      if(!standings.length){$('season').add(new Option('No enrolled seasons',''));$('season').disabled=true;}
      drawSeason();
    }).catch(error=>{
      $('season').disabled=true;$('chart-measure').disabled=true;
      message('metrics','Season statistics unavailable.',true);message('standings','Standings unavailable. Reload to retry.',true);say(error.message);
    });
    api('/api/reports/v_player_totals').then(data=>{
      $('leaders').replaceChildren();
      const rows=knownGoalLeaders(data.rows);
      const max=Math.max(1,...rows.map(row=>Number(row.recorded_goals)));
      for(const [i,row] of rows.entries()) {
        const line=el('div');line.className='leader';
        const rank=el('span',String(i+1).padStart(2,'0'));rank.className='rank';
        const player=el('div');player.className='player';player.append(el('strong',row.full_name),el('small',row.team_name+' · '+row.position));
        const coverage=statCoverage(row,'goal');if(coverage)player.append(el('small',coverage));
        const meter=el('span');meter.className='player-meter';meter.setAttribute('aria-hidden','true');
        const fill=el('span');fill.style.width=(Number(row.recorded_goals)/max*100)+'%';meter.append(fill);player.append(meter);
        line.append(rank,player,el('b',row.recorded_goals));$('leaders').append(line);
      }
      if(!rows.length)message('leaders','No known player totals yet. Import player statistics to populate this panel.');
    }).catch(error=>{message('leaders','Player totals unavailable. Reload to retry.',true);say(error.message);});
  }
}
