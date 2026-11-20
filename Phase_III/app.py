import csv
import io
import json
import os
import re
import secrets
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from xml.sax.saxutils import escape

import click
import pymysql
from dotenv import load_dotenv
from flask import Flask, abort, g, jsonify, render_template, request, session, Response
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash
from reportlab.lib.pagesizes import landscape, A3
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, LongTable, TableStyle
from reportlab.lib import colors

load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
                  PERMANENT_SESSION_LIFETIME=timedelta(hours=4), MAX_CONTENT_LENGTH=65536)
FIELDS = {k:v.split() for k,v in {
    'users':'user_id display_name email role', 'teams':'team_id team_name city',
    'competitions':'competition_id competition_name competition_type country',
    'seasons':'season_id competition_id season_label start_date end_date',
    'season_teams':'season_id team_id', 'players':'player_id team_id full_name position',
    'matches':'match_id season_id home_team_id away_team_id kickoff_at match_status home_score away_score',
    'player_match_stats':'match_id player_id minutes_played goals assists'}.items()}
KEYS = {t: fields[:2 if t in ('season_teams','player_match_stats') else 1] for t,fields in FIELDS.items()}
VIEWS = ['v_'+x for x in 'match_details above_any_team_goal_total players_with_goals match_stat_coverage goal_or_assist_players league_standings player_totals match_results scheduled_fixtures team_home_away'.split()]
GUEST = [VIEWS[7],VIEWS[8]]
OPTIONS = {'role':['ADMIN','USER','GUEST'],'position':['GK','DEF','MID','FWD'],
           'match_status':['SCHEDULED','COMPLETED'],'competition_type':['LEAGUE','CUP']}
CLUBS = {57:'Arsenal',61:'Chelsea',64:'Liverpool',65:'Manchester City',66:'Manchester United',73:'Tottenham Hotspur'}

def api_football_enabled():
    provider=os.getenv('TOUCHLINE_PROVIDER','football-data.org')
    if provider not in ('football-data.org','api-football'):
        abort(503,'TOUCHLINE_PROVIDER must be football-data.org or api-football.')
    return provider=='api-football'

def db():
    if 'db' not in g:
        g.db = pymysql.connect(host=os.getenv('MYSQL_HOST','localhost'), port=int(os.getenv('MYSQL_PORT','3306')),
            user=os.environ.get('MYSQL_USER','group12'), password=os.getenv('MYSQL_PASSWORD',''),
            database=os.getenv('MYSQL_DATABASE','group12_football_phase2'), charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,connect_timeout=5)
    return g.db

@app.teardown_appcontext
def close(error):
    if 'db' in g: g.db.close()

def sql(stmt,args=()):
    with db().cursor() as cur:
        cur.execute(stmt,args)
        return list(cur.fetchall()) if cur.description else []

def clean(rows):
    return [{k:(v.isoformat() if isinstance(v,date) else int(v) if isinstance(v,Decimal) else v)
             for k,v in row.items()} for row in rows]

@app.errorhandler(Exception)
def failure(e):
    if isinstance(e,HTTPException): return jsonify(error=e.description),e.code
    if isinstance(e,pymysql.IntegrityError): return jsonify(error='Duplicate key or dependent record. Check the IDs and references.'),409
    if isinstance(e,pymysql.DataError): return jsonify(error='Value outside the database field limits.'),400
    if isinstance(e,pymysql.MySQLError): return jsonify(error='Database request failed. Check the connection, schema and migration.'),503
    app.logger.exception('Request failed')
    return jsonify(error='Unexpected application error.'),500

@app.before_request
def protect():
    if request.method in ('POST','PUT','DELETE') and (not session.get('csrf') or request.headers.get('X-CSRF-Token') != session['csrf']):
        abort(403,'Reload the page before submitting.')
    if request.endpoint in ('records','reports','imports','page') and request.path != '/login':
        if 'uid' not in session:
            if request.endpoint=='page':
                from flask import redirect
                return redirect('/login')
            abort(401,'Please sign in.')
        u=sql('SELECT user_id,display_name,role FROM users JOIN web_sessions USING(user_id) WHERE user_id=%s AND session_id=%s AND expires_at>UTC_TIMESTAMP()',[session['uid'],session.get('sid')])
        if not u: session.clear(); abort(401,'Please sign in again.')
        g.user=u[0]
        if (request.endpoint in ('records','imports') or request.path in ('/manage','/import')) and g.user['role']!='ADMIN':
            abort(403,'Administrator access required.')

@app.get('/')
@app.get('/login')
@app.get('/reports')
@app.get('/manage')
@app.get('/import')
def page():
    return render_template('page.html',path=request.path,csrf=session.setdefault('csrf',secrets.token_hex(24)),
        user=g.get('user',{}),views=GUEST if g.get('user',{}).get('role')=='GUEST' else VIEWS,
        fields=FIELDS,keys=KEYS,options=OPTIONS,api_football_enabled=api_football_enabled(),
        active_season='2023/24' if api_football_enabled() else '2025/26')

def body():
    data=request.get_json(silent=True)
    if not isinstance(data,dict): abort(400,'Expected a JSON object.')
    return data

@app.post('/api/login')
def login():
    d=body()
    if not all(isinstance(d.get(k),str) for k in ('email','password')): abort(400,'Enter email and password.')
    u=sql('SELECT user_id,password_hash FROM users JOIN login_credentials USING(user_id) WHERE email=%s',[d['email']])
    if not u or not check_password_hash(u[0]['password_hash'],d['password']): abort(401,'Incorrect email or password.')
    session.clear(); session.permanent=True; session['uid']=u[0]['user_id']
    session['sid']=secrets.token_hex(32)
    sql('DELETE FROM web_sessions WHERE expires_at<=UTC_TIMESTAMP()')
    sql('INSERT INTO web_sessions VALUES (%s,%s,UTC_TIMESTAMP()+INTERVAL 4 HOUR)',[session['sid'],session['uid']])
    db().commit()
    return jsonify(ok=True)

@app.post('/api/logout')
def logout():
    if session.get('sid'):
        sql('DELETE FROM web_sessions WHERE session_id=%s',[session['sid']])
        db().commit()
    session.clear()
    return jsonify(ok=True)

@app.cli.command('demo-accounts')
def demo():
    """Generate a one-time password for each existing Phase II demo role."""
    created=[]
    for email,role in [('admin.one@example.com','ADMIN'),('reader.one@example.com','USER'),('guest.one@example.com','GUEST')]:
        rows=sql('SELECT user_id FROM users WHERE email=%s AND role=%s',[email,role])
        if not rows: raise click.ClickException('Missing demo user: '+email)
        uid=rows[0]['user_id']
        if sql('SELECT user_id FROM login_credentials WHERE user_id=%s',[uid]): continue
        pw=secrets.token_urlsafe(15)
        sql('INSERT INTO login_credentials VALUES (%s,%s)',[uid,generate_password_hash(pw)])
        created.append((email,pw))
    db().commit()
    for email,pw in created: click.echo(f'{email}  {pw}')

@app.cli.command('reset-demo-passwords')
def reset_demo_passwords():
    """Reset only the three existing demo credentials; display passwords once."""
    if not sys.stdout.isatty():
        raise click.ClickException('Run in an interactive local terminal; do not redirect output.')
    targets=[('admin.one@example.com','ADMIN'),
             ('reader.one@example.com','USER'),
             ('guest.one@example.com','GUEST')]
    generated=[]
    try:
        # Lock and validate all targets before changing any hash.
        accounts=[]
        for email,role in targets:
            rows=sql('SELECT u.user_id,u.role FROM users u JOIN login_credentials lc USING(user_id) WHERE u.email=%s FOR UPDATE',[email])
            if len(rows)!=1 or rows[0]['role']!=role:
                raise click.ClickException('Expected existing user, role and credential not found: '+email)
            accounts.append((email,rows[0]['user_id']))
        used=set()
        for email,uid in accounts:
            password=secrets.token_urlsafe(24)
            while password in used:
                password=secrets.token_urlsafe(24)
            used.add(password)
            password_hash=generate_password_hash(password)
            sql('UPDATE login_credentials SET password_hash=%s WHERE user_id=%s',[password_hash,uid])
            saved=sql('SELECT password_hash FROM login_credentials WHERE user_id=%s',[uid])
            if len(saved)!=1 or not check_password_hash(saved[0]['password_hash'],password):
                raise click.ClickException('Password verification failed; reset cancelled.')
            generated.append((email,password))
        db().commit()
    except Exception:
        db().rollback()
        # Never print database exceptions: drivers can include query parameters.
        raise click.ClickException('Reset did not complete. Verify the three existing accounts and database access. No passwords will be displayed.') from None
    click.echo('All three passwords were reset. Save these privately; they are shown only here:')
    for email,password in generated:
        click.echo(email+'  '+password)


def validate(table,d,create):
    allowed=set(FIELDS[table]) | ({'password'} if table=='users' else set())
    if d.keys()-allowed: abort(400,'Unknown field.')
    result={}
    for k in FIELDS[table]:
        v=d.get(k)
        if k in ('home_score','away_score') and v in (None,''): result[k]=None; continue
        if v is None or isinstance(v,(dict,list,bool)) or str(v).strip()=='': abort(400,'Required: '+k)
        v=str(v).strip()
        if k.endswith('_id') or k in ('minutes_played','goals','assists','home_score','away_score'):
            if not re.fullmatch(r'[0-9]{1,10}',v): abort(400,'Expected a whole number: '+k)
            v=int(v)
            lo,hi=(1,2147483647) if k.endswith('_id') else (1,120) if k=='minutes_played' else (0,20) if k in ('goals','assists') else (0,255)
            if not lo<=v<=hi: abort(400,'Out of range: '+k)
        elif k in OPTIONS and v not in OPTIONS[k]: abort(400,'Invalid '+k)
        elif k=='email' and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',v): abort(400,'Invalid email.')
        elif k=='season_label' and not re.fullmatch(r'\d{4}/\d{2}',v): abort(400,'Use YYYY/YY.')
        elif k in ('start_date','end_date','kickoff_at'):
            try:
                v=datetime.fromisoformat(v) if k=='kickoff_at' else date.fromisoformat(v)
            except ValueError: abort(400,'Invalid date or time: '+k)
            if isinstance(v,datetime) and (v.tzinfo or len(str(d[k]))<16): abort(400,'Enter kickoff as a UTC date and time.')
        elif len(v)>{'display_name':80,'email':254,'country':60,'city':80}.get(k,100): abort(400,'Too long: '+k)
        result[k]=v
    if table=='users' and (create or d.get('password')):
        if not isinstance(d.get('password'),str) or not 10<=len(d['password'])<=256: abort(400,'Use a password of 10 to 256 characters.')
    if table=='seasons' and result['start_date']>=result['end_date']: abort(400,'Season end must follow its start.')
    if table=='matches':
        if result['home_team_id']==result['away_team_id']: abort(400,'Choose two different clubs.')
        for k in ('home_score','away_score'):
            if (result[k] is None)!=(result['match_status']=='SCHEDULED'): abort(400,'Completed matches need both scores. Scheduled matches have blank scores.')
    return result

def integrity():
    invalid=sql("""SELECT m.match_id FROM player_match_stats s JOIN matches m USING(match_id)
        JOIN players p USING(player_id) GROUP BY m.match_id,p.team_id,m.home_team_id,m.away_team_id,
        m.match_status,m.home_score,m.away_score HAVING m.match_status<>'COMPLETED'
        OR p.team_id NOT IN(m.home_team_id,m.away_team_id)
        OR SUM(s.goals)>IF(p.team_id=m.home_team_id,m.home_score,m.away_score) LIMIT 1""")
    if invalid: abort(409,'Player stats must belong to a participating club in a completed match and fit its score.')
    if sql('SELECT match_id FROM matches JOIN seasons USING(season_id) WHERE DATE(kickoff_at) NOT BETWEEN start_date AND end_date LIMIT 1'):
        abort(409,'Kickoff must fall inside the season.')

@app.route('/api/records/<table>',methods=['GET','POST'])
@app.route('/api/records/<table>/<key>',methods=['GET','PUT','DELETE'])
def records(table,key=None):
    if table not in FIELDS: abort(404)
    cols=FIELDS[table]; keys=KEYS[table]; ids=key.split(',') if key else []
    if key and (len(ids)!=len(keys) or not all(re.fullmatch('[0-9]{1,10}',i) for i in ids)): abort(400,'Invalid record key.')
    cond=' AND '.join(k+'=%s' for k in keys)
    where=' WHERE '+cond if key else ''
    if request.method=='GET':
        extra=',is_synthetic' if table in ('matches','player_match_stats') else ''
        rows=sql('SELECT '+','.join(cols)+extra+' FROM '+table+where+' ORDER BY '+','.join(keys),ids)
        if key and not rows: abort(404)
        return jsonify(clean(rows))
    if key and not sql('SELECT '+keys[0]+' FROM '+table+where+' FOR UPDATE',ids): abort(404,'Record does not exist.')
    if key and table=='matches' and sql('SELECT match_id FROM imported_matches WHERE match_id=%s',ids):
        abort(409,'Imported matches are maintained by the provider.')
    if key and table=='matches' and api_football_enabled() and sql('SELECT match_id FROM provider_matches WHERE match_id=%s',ids):
        abort(409,'Imported matches are maintained by the provider.')
    if request.method=='DELETE':
        if table=='users' and int(ids[0])==session['uid']: abort(409,'You cannot delete your own account.')
        sql('DELETE FROM '+table+where,ids)
    else:
        d=body(); vals=validate(table,d,key is None)
        if key and table=='users' and int(ids[0])==session['uid'] and vals['role']!='ADMIN': abort(409,'You cannot demote your own account.')
        if key:
            if len(keys)==1 and str(vals[keys[0]])!=ids[0]: abort(400,'Record ID cannot change.')
            sql('UPDATE '+table+' SET '+','.join(k+'=%s' for k in cols)+where,list(vals.values())+ids)
        else:
            sql('INSERT INTO '+table+' ('+','.join(cols)+') VALUES ('+','.join(['%s']*len(cols))+')',list(vals.values()))
        if table=='users' and d.get('password'):
            sql('DELETE FROM web_sessions WHERE user_id=%s',[vals['user_id']])
            sql('INSERT INTO login_credentials VALUES (%s,%s) ON DUPLICATE KEY UPDATE password_hash=%s',
                [vals['user_id']]+[generate_password_hash(d['password'])]*2)
        if table in ('seasons','players','matches','player_match_stats'): integrity()
    db().commit()
    return jsonify(ok=True),201 if request.method=='POST' else 200

