import hashlib
from app import (app,db,sql,body,clean,g,abort,request,jsonify,session,VIEWS,GUEST,CLUBS,Response,
                 os,json,datetime,timezone,Request,urlopen,HTTPError,URLError,csv,io,escape,
                 SimpleDocTemplate,Paragraph,LongTable,TableStyle,colors,landscape,A3,getSampleStyleSheet,integrity)

@app.get('/api/reports/<name>')
def reports(name):
    if name not in VIEWS: abort(404)
    fmt=request.args.get('format','json')
    if fmt not in ('json','csv','pdf'): abort(400,'Unknown format.')
    if g.user['role']=='GUEST' and (name not in GUEST or fmt!='json'): abort(403,'This report or export requires a user account.')
    cols=[r['Field'] for r in sql('SHOW COLUMNS FROM '+name)]
    q=request.args.get('q','').strip()
    field=request.args.get('field','')
    if field and field not in cols: abort(400,'Unknown search field.')
    where=''; args=[]
    if q:
        fields=[field] if field else cols
        where=' WHERE '+' OR '.join('LOCATE(%s, CAST(`'+c+'` AS CHAR))>0' for c in fields)
        args=[q]*len(fields)
    order='season_id,league_position' if name==VIEWS[5] else 'recorded_goals DESC,player_id' if name in (VIEWS[1],VIEWS[6]) else ','.join('`'+c+'`' for c in cols[:2])
    rows=clean(sql('SELECT * FROM '+name+where+' ORDER BY '+order,args))
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
        doc.build([Paragraph(title,styles['Title']),Paragraph('Course dataset, including fictional sample records.',styles['BodyText']),table])
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

