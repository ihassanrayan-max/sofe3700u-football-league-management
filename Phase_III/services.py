import hashlib
import api_football as af
from provider_store import save_snapshot
from app import (app,db,sql,body,clean,g,abort,request,jsonify,session,VIEWS,GUEST,CLUBS,Response,api_football_enabled,
                 os,json,datetime,timezone,Request,urlopen,HTTPError,URLError,csv,io,escape,
                 SimpleDocTemplate,Paragraph,LongTable,TableStyle,colors,landscape,A3,getSampleStyleSheet,integrity)

@app.get('/api/reports/<name>')
def reports(name):
    if name not in VIEWS: abort(404)
    fmt=request.args.get('format','json')
    if fmt not in ('json','csv','pdf'): abort(400,'Unknown format.')
    if g.user['role']=='GUEST' and (name not in GUEST or fmt!='json'): abort(403,'This report or export requires a user account.')
    source='tl_'+name if api_football_enabled() else name
    cols=[r['Field'] for r in sql('SHOW COLUMNS FROM '+source)]
    q=request.args.get('q','').strip()
    field=request.args.get('field','')
    if field and field not in cols: abort(400,'Unknown search field.')
    where=''; args=[]
    if q:
        fields=[field] if field else cols
        where=' WHERE '+' OR '.join('LOCATE(%s, CAST(`'+c+'` AS CHAR))>0' for c in fields)
        args=[q]*len(fields)
    order='season_id,league_position' if name==VIEWS[5] else 'recorded_goals DESC,player_id' if name in (VIEWS[1],VIEWS[6]) else ','.join('`'+c+'`' for c in cols[:2])
    rows=clean(sql('SELECT * FROM '+source+where+' ORDER BY '+order,args))
    if fmt=='json': return jsonify(columns=cols,rows=rows)
    matrix=[[c.replace('_',' ').title() for c in cols]]+[[str(row[c]) if row[c] is not None else '' for c in cols] for row in rows]
    title=name[2:].replace('_',' ').title()
    if fmt=='csv':
        buf=io.StringIO(); writer=csv.writer(buf)
        for row in matrix: writer.writerow(["'"+v if v.startswith(('=','+','@','-','\t','\r')) and not v.lstrip('-').isdigit() else v for v in row])
        data=buf.getvalue(); mime='text/csv'
    else:
        buf=io.BytesIO(); doc=SimpleDocTemplate(buf,pagesize=landscape(A3),leftMargin=28,rightMargin=28)
        styles=getSampleStyleSheet()
        table=LongTable([[Paragraph(escape(v),styles['BodyText']) for v in row] for row in matrix],colWidths=[doc.width/len(cols)]*len(cols),repeatRows=1)
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('VALIGN',(0,0),(-1,-1),'TOP')]))
        note='API-Football EPL 2023/24: six-club subset; partial player coverage. Blank statistics are unknown.' if api_football_enabled() else 'Course dataset, including fictional sample records.'
        doc.build([Paragraph(title,styles['Title']),Paragraph(note,styles['BodyText']),table])
        data=buf.getvalue(); mime='application/pdf'
    return Response(data,mimetype=mime,headers={'Content-Disposition':f'attachment; filename="{name}.{fmt}"'})

def fetch_matches():
    token=os.getenv('FOOTBALL_DATA_TOKEN')
    if not token: abort(503,'Set FOOTBALL_DATA_TOKEN and restart the app.')
    req=Request('https://api.football-data.org/v4/competitions/PL/matches?season=2025',headers={'X-Auth-Token':token})
    try:
        with urlopen(req,timeout=15) as response: payload=json.load(response)
    except HTTPError as e:
        if e.code==429: abort(429,'Provider rate limit reached. Wait before retrying.')
        if e.code in (401,403): abort(502,'Provider denied access. Check token and historical season coverage.')
        abort(502,'Football provider returned an error.')
    except (URLError,TimeoutError,ValueError): abort(502,'Provider unavailable or response unreadable.')
    if not isinstance(payload,dict) or not isinstance(payload.get('matches'),list): abort(502,'Missing match list.')
    if not payload['matches']: abort(422,'No fixtures returned for 2025/26. Check season access.')
    rows=[]; skipped=0
    for m in payload['matches']:
        try:
            h=CLUBS.get(m['homeTeam']['id']); a=CLUBS.get(m['awayTeam']['id'])
            if not h or not a: continue
            if m['competition']['code']!='PL' or m['season']['startDate'][:4]!='2025' or h==a: raise ValueError()
            status={'FINISHED':'COMPLETED','TIMED':'SCHEDULED','SCHEDULED':'SCHEDULED'}[m['status']]
            dt=datetime.fromisoformat(m['utcDate'].replace('Z','+00:00'))
            if not dt.tzinfo or type(m['id'])!=int or m['id']<=0: raise ValueError()
            goals=[m['score']['fullTime'][k] for k in ('home','away')] if status=='COMPLETED' else [None,None]
            if status=='COMPLETED' and not all(type(n)==int and 0<=n<=255 for n in goals): raise ValueError()
            rows.append(dict(external_id=m['id'],home_team=h,away_team=a,kickoff_at=dt.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),match_status=status,home_score=goals[0],away_score=goals[1]))
        except (TypeError,KeyError,ValueError,AttributeError): skipped+=1
    if not rows: abort(422,'No supported six-club fixtures in this response.')
    if len({r['external_id'] for r in rows})!=len(rows): abort(502,'Provider returned duplicate fixture IDs.')
    return sorted(rows,key=lambda r:r['external_id']),skipped

@app.route('/api/import/<action>',methods=['GET','POST'])
def imports(action):
    if not api_football_enabled(): return legacy_imports(action)
    if (action,request.method)==('statistics','GET'):
        key=request.args.get('match_id','')
        if not key.isdigit(): abort(400,'Select a saved match ID.')
        rows=sql('SELECT t.team_name,s.details FROM provider_team_stats s JOIN teams t USING(team_id) JOIN tl_matches m USING(match_id) WHERE s.match_id=%s ORDER BY t.team_name',[key])
        result=[]
        for row in rows:
            for stat in json.loads(row['details']):
                result.append(dict(team=row['team_name'],statistic=stat['type'],value=stat['value']))
        return jsonify(result)
    if (action,request.method)==('history','GET'):
        return jsonify(clean(sql("SELECT i.provider,i.external_id,v.*,e.player_count,e.team_count FROM provider_matches i JOIN tl_v_match_details v USING(match_id) LEFT JOIN provider_enrichment e USING(match_id) WHERE i.provider='api-football' ORDER BY kickoff_at")))
    if request.method!='POST' or action not in ('preview','save'): abort(404)
    data=body()
    cache=af.Cache()
    if action=='save':
        digest=session.get('api_football_preview')
        if not digest or data.get('preview_id')!=digest:
            abort(409,'Preview changed or belongs to another tab. Fetch and review a new preview.')
        saved=cache.get('preview:'+digest) if digest else None
        if saved is None: abort(409,'Fetch a new preview; previews expire after one hour.')
        if not saved['fixtures']: abort(409,'This preview contains no eligible records to save.')
        count=save_snapshot(sql,db(),saved)
        session.pop('api_football_preview',None)
        return jsonify(saved=count)
    session.pop('api_football_preview',None)
    kind=data.get('kind','fixtures')
    if kind not in ('fixtures','enrichment'): abort(400,'Unknown preview kind.')
    rows,skipped=af.parse_fixtures(cache.fetch('fixtures',league=39,season=2023))
    if kind=='enrichment':
        # At most two fixtures per explicit preview: four additional requests.
        pending=sql("SELECT i.external_id FROM provider_matches i JOIN tl_matches m USING(match_id) LEFT JOIN provider_enrichment e USING(match_id) WHERE i.provider='api-football' AND m.match_status='COMPLETED' AND e.match_id IS NULL ORDER BY i.external_id LIMIT 2")
        ids={r['external_id'] for r in pending}
        rows=[r for r in rows if r['external_id'] in ids]
        for row in rows:
            row['players']=af.parse_players(cache.fetch('fixtures/players',fixture=row['external_id']),row)
            row['team_stats']=af.parse_team_stats(cache.fetch('fixtures/statistics',fixture=row['external_id']),row)
    digest=af.snapshot(cache,{'fixtures':rows})
    session['api_football_preview']=digest
    preview=[{k:v for k,v in row.items() if k not in ('players','team_stats')} | ({'player_records':len(row['players']),'team_stat_records':len(row['team_stats'])} if 'players' in row else {}) for row in rows]
    return jsonify(rows=preview,skipped=skipped,preview_id=digest)


def legacy_imports(action):
    """Existing importer remains available until the explicit provider cutover."""
    if (action,request.method)==('history','GET'):
        return jsonify(clean(sql('SELECT i.external_id,v.* FROM imported_matches i JOIN v_match_details v USING(match_id) ORDER BY kickoff_at')))
    if request.method!='POST' or action not in ('preview','save'): abort(404)
    rows,skipped=fetch_matches()
    digest=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
    if action=='preview':
        session['preview']=digest
        return jsonify(rows=rows,skipped=skipped)
    if session.get('preview')!=digest: abort(409,'Preview the current provider data before saving.')
    members=sql("""SELECT s.season_id,t.team_name,t.team_id FROM seasons s JOIN competitions c USING(competition_id)
        JOIN season_teams st USING(season_id) JOIN teams t USING(team_id)
        WHERE c.competition_name='Premier League' AND s.season_label='2025/26' FOR UPDATE""")
    teams={m['team_name']:m['team_id'] for m in members}
    if not set(CLUBS.values())<=teams.keys(): abort(409,'Restore the six original Premier League memberships first.')
    season=members[0]['season_id']
    # Lock the largest match ID before allocating IDs in the Phase II schema.
    top=sql('SELECT match_id FROM matches ORDER BY match_id DESC LIMIT 1 FOR UPDATE')
    next_id=top[0]['match_id']+1 if top else 1
    for r in rows:
        info=[season,teams[r['home_team']],teams[r['away_team']],r['kickoff_at'],r['match_status'],r['home_score'],r['away_score']]
        old=sql('SELECT match_id FROM imported_matches WHERE external_id=%s FOR UPDATE',[r['external_id']])
        if old:
            sql('UPDATE matches SET season_id=%s,home_team_id=%s,away_team_id=%s,kickoff_at=%s,match_status=%s,home_score=%s,away_score=%s WHERE match_id=%s',info+[old[0]['match_id']])
        else:
            sql('INSERT INTO matches (match_id,season_id,home_team_id,away_team_id,kickoff_at,match_status,home_score,away_score,is_synthetic) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,0)',[next_id]+info)
            sql('INSERT INTO imported_matches VALUES (%s,%s)',[r['external_id'],next_id])
            next_id+=1
    integrity(); db().commit(); session.pop('preview',None)
    return jsonify(saved=len(rows))

