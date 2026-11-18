const $ = id => document.getElementById(id);
const cfg = JSON.parse($('config').textContent);
const title = s => s.replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase());
const say = text => $('feedback').textContent=text;
const el = (tag,text) => {const e=document.createElement(tag); if(text!=null)e.textContent=text;return e;};
async function api(path,method='GET',data){
  const response=await fetch(path,{method,headers:{'Content-Type':'application/json','X-CSRF-Token':cfg.csrf},body:data===undefined?undefined:JSON.stringify(data)});
  const result=await response.json();
  if(!response.ok)throw Error(result.error || 'Request failed.');
  return result;
}
function run(fn){return async event=>{event?.preventDefault();try{say('');await fn(event);}catch(e){say(e.message);}};}
function grid(target,cols,rows,actions){
  const wrap=el('div');wrap.className='scroll';const table=el('table'),head=table.createTHead().insertRow();
  for(const col of cols)head.append(el('th',title(col)));
  if(actions)head.append(el('th','Actions'));
  const body=table.createTBody();
  for(const row of rows){const tr=body.insertRow();for(const col of cols)tr.insertCell().textContent=col==='is_synthetic'?(row[col]?'Yes':'No'):row[col]??'—';if(actions)actions(tr.insertCell(),row);}
  wrap.append(table);$(target).replaceChildren(wrap);if(!rows.length)$(target).append(el('p','No matching records.'));
}
if($('login'))$('login').onsubmit=run(async()=>{await api('/api/login','POST',Object.fromEntries(new FormData($('login'))));location.assign('/');});
if($('logout'))$('logout').onclick=run(async()=>{await api('/api/logout','POST',{});location.assign('/login');});
if($('report')){
  async function report(reset){
    if(reset){$('field').replaceChildren(new Option('All fields',''));$('search').value='';}
    const params=new URLSearchParams({q:$('search').value,field:$('field').value});
    const url='/api/reports/'+$('report').value+'?'+params;
    const {rows,columns}=await api(url);grid('grid',columns,rows);
    if(reset)for(const c of columns)$('field').add(new Option(title(c),c));
    for(const fmt of ['csv','pdf'])if($(fmt))$(fmt).href=url+'&format='+fmt;
  }
  $('report').onchange=run(()=>report(true));$('apply').onclick=run(()=>report(false));run(()=>report(true))();
}
if($('entity')){
  let selected=null;
  function form(row){
    const t=$('entity').value;selected=row?cfg.keys[t].map(k=>row[k]).join(','):null;
    $('inputs').replaceChildren();$('save').textContent=row?'Save changes':'Create record';
    for(const k of [...cfg.fields[t],...(t==='users'?['password']:[])]){
      const l=el('label',title(k)+(row&&k==='password'?' (optional)':''));let input;
      if(cfg.options[k]){input=el('select');for(const v of cfg.options[k])input.add(new Option(v,v));}
      else{input=el('input');input.type=k==='email'?'email':k==='password'?'password':k==='kickoff_at'?'datetime-local':k.endsWith('_date')?'date':k.endsWith('_id')||['goals','assists','minutes_played','home_score','away_score'].includes(k)?'number':'text';
        if(input.type==='number')input.min=k.endsWith('_id')||k==='minutes_played'?1:0;if(k==='password')input.minLength=10;if(k==='kickoff_at')input.step=1;}
      input.name=k;input.required=!['home_score','away_score'].includes(k)&&!(row&&k==='password');
      if(row&&row[k]!=null)input.value=row[k];if(row&&cfg.keys[t].length===1&&cfg.keys[t].includes(k))input.readOnly=true;
      l.append(input);$('inputs').append(l);
    }
  }
  async function refresh(){
    const t=$('entity').value;form(null);const rows=await api('/api/records/'+t);
    grid('grid',Object.keys(rows[0]||Object.fromEntries(cfg.fields[t].map(k=>[k,null]))),rows,(td,row)=>{
      const edit=el('button','Edit'),del=el('button','Delete');td.append(edit,' ',del);edit.onclick=()=>{form(row);$('editor').scrollIntoView();};
      del.onclick=run(async()=>{const key=cfg.keys[t].map(k=>row[k]).join(',');if(!confirm('Delete '+t+' record '+key+'?'))return;
        await api('/api/records/'+t+'/'+key,'DELETE');await refresh();say('Record deleted.');});
    });
  }
  $('clear').onclick=()=>form(null);$('entity').onchange=run(refresh);
  $('editor').onsubmit=run(async()=>{const t=$('entity').value;await api('/api/records/'+t+(selected?'/'+selected:''),selected?'PUT':'POST',Object.fromEntries(new FormData($('editor'))));await refresh();say('Record saved.');});
  run(refresh)();
}
if($('preview')){
  async function history(){const rows=await api('/api/import/history');grid('history',Object.keys(rows[0]||{external_id:0,match_id:0}),rows);}
  $('preview').onclick=run(async()=>{$('commit').disabled=true;const d=await api('/api/import/preview','POST',{});grid('grid',Object.keys(d.rows[0]),d.rows);$('commit').disabled=false;say(d.rows.length+' eligible fixtures. '+d.skipped+' incomplete or unsupported records skipped.');});
  $('commit').onclick=run(async()=>{$('commit').disabled=true;const d=await api('/api/import/save','POST',{});await history();say('Saved '+d.saved+' fixtures.');});run(history)();
}
if(location.pathname==='/')run(async()=>{
  const d=await api('/api/reports/v_match_results');grid('grid',d.columns,d.rows);
  if($('chart')){const s=await api('/api/reports/v_league_standings');new Chart($('chart'), {
      type:'bar', data:{labels:s.rows.map(r=>r.team_name),datasets:[{label:'Points',data:s.rows.map(r=>r.points),backgroundColor:'#247955'}]},
      options:{indexAxis:'y',scales:{x:{beginAtZero:true,ticks:{precision:0}}}}
    });
  }
})();